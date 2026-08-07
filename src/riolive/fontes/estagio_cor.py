"""Estágio operacional da cidade (COR).

JSON não documentado achado no HTML do cor.rio: `appcor.cor-rio.work/estagio_cidade`
→ {"cor": "#...", "estagio": "Estágio N", "mensagem": ..., "id": N, "inicio": ISO-Z}.
Domínio interno: tratar como frágil; fallback documentado = raspar o site do COR.

**O campo `id` NÃO é o estágio.** Em 2026-08-06 a cidade subiu pra Estágio 2 e o
`id` continuou 1, enquanto o texto e a cor acompanharam. Um crosscheck que exigia
`id` == texto derrubou a fonte de criticidade 5 por um dia inteiro, recusando dado
bom por causa do campo errado. Quem manda é o **texto** — é o que o COR publica;
o `id` virou metadado no payload. Lição: crosscheck que desliga a fonte tem que
ser sobre o que invalida o dado, não sobre um campo acessório.

A **cor** corrobora, mas nunca reprova: se divergir, loga e segue. Só duas cores
foram observadas de verdade (verde no 1, amarelo no 2); as dos estágios 3 a 5
ficam de fora até serem vistas — mapa inventado vira falso positivo.

O `inicio` vem com sufixo `Z` e aqui o `Z` é **UTC de verdade** — conferido em
2026-08-07 contra a publicação do próprio COR ("Estágio 2 às 19h00 desta
quinta-feira, 6 de agosto"): 19h00 local = 22h00 UTC, e a API devolveu
`2026-08-06T22:08:57Z`. Não confundir com o GPS SPPO, onde o `Z` é mentira.

Severidade 1 a 5 espelha LITERALMENTE o estágio (a escala nativa da cidade).
Evento "vigente": só existe um aberto; mudança de estágio fecha o anterior.
Sem detector de congelamento: Estágio 1 pode durar semanas — dado parado é normal.
"""

import json
import logging
import re
from datetime import datetime, timedelta

from pydantic import BaseModel

from riolive.ingestao.contrato import (
    ErroSchema,
    EventoNovo,
    FonteConfig,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp

logger = logging.getLogger(__name__)

URL = "https://appcor.cor-rio.work/estagio_cidade"

# Só o que foi visto ao vivo. Estágios 3 a 5 entram quando acontecerem.
COR_DO_ESTAGIO = {"#228d46": 1, "#f2c94c": 2}


class EstagioCor(BaseModel):
    """Schema do JSON do estágio da cidade."""

    estagio: str  # "Estágio N" — a fonte da verdade
    cor: str
    id: int | None = None  # NÃO é o estágio; guardado só como metadado
    mensagem: str = ""
    inicio: datetime


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    resposta = cliente.obter(URL)
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} no estágio do COR")
    try:
        bruto = resposta.json()
    except json.JSONDecodeError as exc:
        raise ErroSchema(f"resposta não é JSON: {exc}") from exc
    dado = EstagioCor.model_validate(bruto)

    numero_no_texto = re.search(r"\d+", dado.estagio)
    if not numero_no_texto:
        raise ErroSchema(f"não achei o número do estágio em {dado.estagio!r}")
    estagio = int(numero_no_texto.group())
    if not 1 <= estagio <= 5:
        raise ErroSchema(f"estágio fora da escala 1 a 5: {estagio}")

    # Corroborações que NUNCA reprovam — a fonte já ficou um dia fora por isso
    esperado_pela_cor = COR_DO_ESTAGIO.get(dado.cor.lower())
    if esperado_pela_cor is not None and esperado_pela_cor != estagio:
        logger.warning(
            "COR: cor %s sugere estágio %s, texto diz %s — seguindo pelo texto",
            dado.cor,
            esperado_pela_cor,
            estagio,
        )
    if dado.id is not None and dado.id != estagio:
        logger.info(
            "COR: id=%s diverge do estágio %s (esperado, id não é o estágio)", dado.id, estagio
        )

    evento = EventoNovo(
        tipo="estagio_cor",
        severidade=estagio,
        inicio=dado.inicio,
        titulo=dado.estagio,
        descricao=dado.mensagem or None,
        payload=bruto,
        vigente=True,  # cidade inteira, um estágio de cada vez
    )
    return ResultadoColeta(eventos=[evento])


FONTE = FonteConfig(
    slug="estagio_cor",
    nome="Estágio operacional da cidade (COR)",
    orgao="Centro de Operações Rio",
    url=URL,
    bloco="A",
    criticidade=5,
    cadencia=timedelta(minutes=5),
    tolerancia_frescor=timedelta(days=365),  # sem noção de frescor: estágio parado é normal
    coletar=coletar,
)
