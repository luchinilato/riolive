"""Estágio operacional da cidade (COR).

JSON não documentado achado no HTML do cor.rio: `appcor.cor-rio.work/estagio_cidade`
→ {"cor": "#...", "estagio": "Estágio N", "mensagem": ..., "id": N, "inicio": ISO-Z}.
Domínio interno: tratar como frágil; fallback documentado = raspar o site do COR.

Severidade 1 a 5 espelha LITERALMENTE o estágio (a escala nativa da cidade).
Evento "vigente": só existe um aberto; mudança de estágio fecha o anterior.
Sem detector de congelamento: Estágio 1 pode durar semanas — dado parado é normal.
"""

import json
import re
from datetime import datetime, timedelta

from pydantic import BaseModel, field_validator

from riolive.ingestao.contrato import (
    ErroSchema,
    EventoNovo,
    FonteConfig,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp

URL = "https://appcor.cor-rio.work/estagio_cidade"


class EstagioCor(BaseModel):
    """Schema do JSON do estágio da cidade."""

    id: int  # 1 a 5 = estágio; é a severidade
    estagio: str
    cor: str
    mensagem: str = ""
    inicio: datetime

    @field_validator("id")
    @classmethod
    def _estagio_valido(cls, valor: int) -> int:
        if not 1 <= valor <= 5:
            raise ValueError(f"estágio fora da escala 1 a 5: {valor}")
        return valor


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    resposta = cliente.obter(URL)
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} no estágio do COR")
    try:
        bruto = resposta.json()
    except json.JSONDecodeError as exc:
        raise ErroSchema(f"resposta não é JSON: {exc}") from exc
    dado = EstagioCor.model_validate(bruto)

    # Crosscheck: o texto "Estágio N" tem que bater com o id
    numero_no_texto = re.search(r"\d+", dado.estagio)
    if numero_no_texto and int(numero_no_texto.group()) != dado.id:
        raise ErroSchema(f"id={dado.id} diverge do texto {dado.estagio!r}")

    evento = EventoNovo(
        tipo="estagio_cor",
        severidade=dado.id,
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
