"""Ocorrências de violência armada — Fogo Cruzado (autorização concedida em 2026-08-06).

Auth JWT: POST /auth/login (email+senha do .env) → accessToken de 3600 s; um
login por rodada é suficiente. Filtro por estado RJ + cidade Rio (UUIDs estáveis
descobertos via /states e /cities em 2026-08-06).

Exibição conforme [[DEC - Exibição de segurança sem salvaguardas de borrão e
atraso]]: pino EXATO (lat/lon da API), sem `visivel_apos`. Severidade: 3 sem
vítima, 4 com vítima (ferida ou morta — detalhe fica no payload). Crédito
obrigatório da fonte nos painéis é requisito dos termos deles (a rotulagem já é
requisito do produto inteiro).
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from riolive.config import config
from riolive.ingestao.contrato import ErroSchema, EventoNovo, FonteConfig, ResultadoColeta
from riolive.ingestao.fetcher import ClienteHttp

URL_BASE = "https://api-service.fogocruzado.org.br/api/v2"
ID_ESTADO_RJ = "b112ffbe-17b3-4ad0-8f2a-2038745d1d14"
ID_CIDADE_RIO = "d1bf56cc-6d85-4e6a-a5f5-0ab3f4074be3"
JANELA_DIAS = 3  # rolagem com sobreposição; o dedup absorve o repetido


def _logar(cliente: ClienteHttp) -> str:
    cfg = config()
    if not cfg.fogo_cruzado_user or not cfg.fogo_cruzado_password.get_secret_value():
        raise RuntimeError("FOGO_CRUZADO_USER/FOGO_CRUZADO_PASSWORD não configurados no .env")
    resposta = cliente._cliente.post(
        f"{URL_BASE}/auth/login",
        json={
            "email": cfg.fogo_cruzado_user,
            "password": cfg.fogo_cruzado_password.get_secret_value(),
        },
    )
    if resposta.status_code not in (200, 201):
        raise ErroSchema(f"login falhou: HTTP {resposta.status_code}")
    token = resposta.json().get("data", {}).get("accessToken")
    if not token:
        raise ErroSchema("login sem accessToken na resposta")
    return str(token)


def interpretar_ocorrencia(bruto: dict[str, Any]) -> EventoNovo:
    vitimas = bruto.get("victims") or []
    humanas = [v for v in vitimas if v.get("type") == "People"]
    mortos = sum(1 for v in humanas if v.get("situation") == "Dead")
    feridos = sum(1 for v in humanas if v.get("situation") == "Wounded")
    severidade = 4 if (mortos or feridos) else 3

    contexto = bruto.get("contextInfo") or {}
    motivo = (contexto.get("mainReason") or {}).get("name")
    bairro = (bruto.get("neighborhood") or {}).get("name") or ""
    acao_policial = bruto.get("policeAction")

    partes_titulo = ["Tiros" if not acao_policial else "Operação policial com tiros"]
    if bairro:
        partes_titulo.append(f"em {bairro.title()}")
    if mortos:
        partes_titulo.append(f"· {mortos} morto{'s' if mortos > 1 else ''}")
    if feridos:
        partes_titulo.append(f"· {feridos} ferido{'s' if feridos > 1 else ''}")

    inicio = datetime.fromisoformat(bruto["date"].replace("Z", "+00:00"))
    return EventoNovo(
        tipo="tiroteio",
        severidade=severidade,
        inicio=inicio,
        fim=inicio,  # registro pontual
        titulo=" ".join(partes_titulo),
        descricao=(motivo and f"Motivo registrado: {motivo}. ") or None,
        lat=float(bruto["latitude"]),  # pino exato, por DEC
        lon=float(bruto["longitude"]),
        payload={
            "id_fogo_cruzado": bruto.get("id"),
            "endereco": bruto.get("address"),
            "acao_policial": acao_policial,
            "presenca_agentes": bruto.get("agentPresence"),
            "motivo": motivo,
            "mortos": mortos,
            "feridos": feridos,
            "recortes": [c.get("name") for c in (contexto.get("clippings") or [])],
        },
    )


def buscar_pagina(
    cliente: ClienteHttp, token: str, pagina: int, inicial: str, final: str | None = None
) -> dict[str, Any]:
    params = {
        "order": "ASC",
        "page": str(pagina),
        "take": "100",
        "idState": ID_ESTADO_RJ,
        "idCities": ID_CIDADE_RIO,
        "initialdate": inicial,
    }
    if final:
        params["finaldate"] = final
    resposta = cliente.obter(
        f"{URL_BASE}/occurrences", params=params, headers={"Authorization": f"Bearer {token}"}
    )
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} nas ocorrências")
    try:
        corpo = resposta.json()
    except json.JSONDecodeError as exc:
        raise ErroSchema(f"resposta não é JSON: {exc}") from exc
    if "data" not in corpo or "pageMeta" not in corpo:
        raise ErroSchema("resposta sem data/pageMeta — formato mudou")
    return dict(corpo)


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    token = _logar(cliente)
    inicial = (datetime.now(tz=UTC) - timedelta(days=JANELA_DIAS)).date().isoformat()
    eventos: list[EventoNovo] = []
    pagina = 1
    while True:
        corpo = buscar_pagina(cliente, token, pagina, inicial)
        eventos.extend(interpretar_ocorrencia(o) for o in corpo["data"])
        if not corpo["pageMeta"].get("hasNextPage"):
            break
        pagina += 1
        if pagina > 20:  # 2.000 ocorrências em 3 dias nunca acontece; trava de sanidade
            raise ErroSchema("paginação sem fim na janela de 3 dias")
    return ResultadoColeta(eventos=eventos)


FONTE = FonteConfig(
    slug="fogo_cruzado",
    nome="Ocorrências de violência armada (Fogo Cruzado)",
    orgao="Instituto Fogo Cruzado",
    url=f"{URL_BASE}/occurrences",
    bloco="C",
    criticidade=5,
    cadencia=timedelta(minutes=5),
    tolerancia_frescor=timedelta(days=365),  # dia sem tiroteio é o melhor cenário, não falha
    coletar=coletar,
)
