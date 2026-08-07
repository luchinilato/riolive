"""Extrai local e vigência dos comunicados do COR — primeiro uso da camada de LLM.

O feed do COR chega como texto redacional e entra no banco **sem pino**: um post
que interdita cinco elevados nomeados vira um evento sem nenhuma coordenada, e
some do mapa. Regex não resolve — os nomes são livres ("Elevado Engenheiro
Freyssinet (Paulo de Frontin)") e a vigência está na prosa ("liberação prevista
para as 5h").

Três salvaguardas, nesta ordem de importância:

1. **Não mexe no `geom` do evento.** A dedup de evento pontual é
   (tipo, início, h3_r8); preencher a geometria depois faria a próxima coleta do
   mesmo post não casar com o que já está gravado e inserir duplicata. O que a
   extração produz vive em `payload.llm`, ao lado do dado da fonte, nunca por
   cima dele.
2. **Coordenada passa por caixa.** O modelo pode "lembrar" a coordenada errada
   com toda a confiança; fora da caixa da região metropolitana, o ponto é
   descartado e sobra o nome do local — que já é mais do que tínhamos.
3. **Falhar é permitido.** Sem chave, sem crédito ou com o provedor fora, o
   evento continua no banco exatamente como a fonte publicou. Enriquecimento
   nunca é pré-requisito.

O que sai daqui é **relato, não medição**: rotulado com modelo e horário de
extração, pra que a interface possa dizer de onde veio.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from riolive.config import config
from riolive.db import sessao
from riolive.fontes.comum import coordenada_plausivel
from riolive.llm.cliente import ClienteLlm, ErroLlm
from riolive.modelos import Evento

logger = logging.getLogger(__name__)

# Tipos de evento que valem a extração: são os que trazem lugar no texto
TIPOS_ALVO = ("interdicao", "comunicado_cor")

INSTRUCAO = """Você extrai informação estruturada de comunicados oficiais do Centro de \
Operações e Resiliência do Rio de Janeiro (COR-Rio).

Devolva os lugares citados no comunicado e a janela de vigência, seguindo estas regras:

- Liste cada via, túnel, elevado, ponte, praça, estádio ou bairro citado como lugar \
afetado. Não liste lugares mencionados de passagem sem relação com o fato.
- Use o nome como aparece no texto, sem abreviar.
- Coordenadas: preencha lat/lon SOMENTE se você tiver certeza razoável da localização \
daquele lugar no município do Rio de Janeiro. Na menor dúvida, use null. Um nome sem \
coordenada é útil; uma coordenada errada é pior que nenhuma.
- Vigência: início e fim em ISO 8601 com fuso -03:00, quando o texto permitir deduzir. \
Se o texto não disser, use null. Não invente horário.
- O resumo é uma frase curta, factual, em português, sem adjetivo de gravidade.
- Você descreve o que o texto diz. Não acrescente informação que não está nele."""

ESQUEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["locais", "inicio", "fim", "resumo"],
    "properties": {
        "locais": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["nome", "tipo", "lat", "lon"],
                "properties": {
                    "nome": {"type": "string"},
                    "tipo": {
                        "type": "string",
                        "enum": [
                            "via",
                            "tunel",
                            "elevado",
                            "ponte",
                            "praca",
                            "estadio",
                            "bairro",
                            "outro",
                        ],
                    },
                    "lat": {"type": ["number", "null"]},
                    "lon": {"type": ["number", "null"]},
                },
            },
        },
        "inicio": {"type": ["string", "null"]},
        "fim": {"type": ["string", "null"]},
        "resumo": {"type": "string"},
    },
}


def _instante(bruto: str | None) -> str | None:
    """Valida o ISO que o modelo devolveu; o que não parseia é descartado."""
    if not bruto:
        return None
    try:
        return datetime.fromisoformat(bruto).isoformat()
    except (TypeError, ValueError):
        logger.warning("llm devolveu data inválida: %r", bruto)
        return None


def _locais_validos(brutos: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Filtra coordenada implausível. Devolve (locais, quantos pontos caíram)."""
    saida: list[dict[str, Any]] = []
    descartados = 0
    for local in brutos:
        nome = (local.get("nome") or "").strip()
        if not nome:
            continue
        lat, lon = local.get("lat"), local.get("lon")
        if lat is not None and lon is not None and not coordenada_plausivel(lat, lon):
            logger.info("coordenada fora da região descartada: %s (%s, %s)", nome, lat, lon)
            lat = lon = None
            descartados += 1
        saida.append({"nome": nome, "tipo": local.get("tipo") or "outro", "lat": lat, "lon": lon})
    return saida, descartados


def _pendentes(s: Any, limite: int) -> list[Evento]:
    """Eventos alvo que ainda não passaram pela extração.

    O `payload.llm` é a marca de idempotência: extraído uma vez, nunca de novo —
    é o que impede a variação entre chamadas de virar dado diferente a cada
    rodada, e o que segura o custo.
    """
    return list(
        s.execute(
            select(Evento)
            .where(
                Evento.tipo.in_(TIPOS_ALVO),
                Evento.payload.is_not(None),
                ~Evento.payload.has_key("llm"),
            )
            .order_by(Evento.inicio.desc())
            .limit(limite)
        )
        .scalars()
        .all()
    )


def rodar(limite: int | None = None, cliente: ClienteLlm | None = None) -> dict[str, Any]:
    """Processa os comunicados pendentes. Devolve contadores pro log do Dagster."""
    cfg = config()
    if not cfg.llm_configurado:
        return {"pulado": "sem RIOLIVE_OPENROUTER_API_KEY"}

    limite = limite or cfg.llm_max_itens_por_rodada
    proprio = cliente is None
    cliente = cliente or ClienteLlm()
    contadores = {
        "processados": 0,
        "com_local": 0,
        "com_coordenada": 0,
        "pontos_descartados": 0,
        "falhas": 0,
        "tokens_entrada": 0,
        "tokens_saida": 0,
        "custo_usd": 0.0,
    }
    try:
        with sessao() as s:
            pendentes = _pendentes(s, limite)
            for evento in pendentes:
                texto = "\n\n".join(p for p in (evento.titulo, evento.descricao) if p)
                try:
                    resposta = cliente.extrair(
                        instrucao=INSTRUCAO,
                        texto=texto,
                        schema=ESQUEMA,
                        nome_schema="comunicado_cor",
                    )
                except ErroLlm as exc:
                    # falha de enriquecimento não é falha do evento: segue pro próximo
                    logger.warning("extração falhou no evento %s: %s", evento.id, exc)
                    contadores["falhas"] += 1
                    continue

                locais, descartados = _locais_validos(resposta.dados.get("locais") or [])
                com_ponto = [x for x in locais if x["lat"] is not None]
                extracao = {
                    "modelo": resposta.modelo,
                    "extraido_em": datetime.now(tz=UTC).isoformat(),
                    "locais": locais,
                    "inicio": _instante(resposta.dados.get("inicio")),
                    "fim": _instante(resposta.dados.get("fim")),
                    "resumo": (resposta.dados.get("resumo") or "").strip() or None,
                    # o consumidor tem que saber que isto é leitura de texto
                    "origem": "extração por modelo de linguagem, não verificada",
                }
                # reatribuição (e não mutação) pro SQLAlchemy enxergar o JSONB novo
                evento.payload = {**(evento.payload or {}), "llm": extracao}

                contadores["processados"] += 1
                contadores["com_local"] += 1 if locais else 0
                contadores["com_coordenada"] += 1 if com_ponto else 0
                contadores["pontos_descartados"] += descartados
                contadores["tokens_entrada"] += resposta.tokens_entrada
                contadores["tokens_saida"] += resposta.tokens_saida
                contadores["custo_usd"] += resposta.custo_usd or 0.0
            s.commit()
    finally:
        if proprio:
            cliente.fechar()

    logger.info("extração de comunicados: %s", contadores)
    return contadores
