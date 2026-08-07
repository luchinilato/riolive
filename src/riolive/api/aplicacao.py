"""API pública de leitura — o contrato que o painel, a fase 3 e o MCP server consomem.

Somente leitura; escrita é papel exclusivo da ingestão. Toda resposta leva
Cache-Control curto: o pico de tráfego bate na borda da CDN (Cloudflare), não
aqui. Eventos saem SEMPRE pela vw_evento_publico (salvaguarda de visivel_apos
como esquema, não como boa vontade).
"""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from riolive.api.rotas import (
    agora,
    ar,
    chuva,
    eventos,
    fontes,
    locais,
    mobilidade,
    posicoes,
    previsao,
    radar,
    seguranca,
    series,
    transito,
)

CACHE_PADRAO_S = 15

app = FastAPI(
    title="riolive — API pública de leitura",
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # API pública, sem credenciais
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cache_na_borda(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    resposta = await call_next(request)
    if request.method == "GET" and "cache-control" not in resposta.headers:
        resposta.headers["Cache-Control"] = f"public, max-age={CACHE_PADRAO_S}"
    return resposta


app.include_router(agora.rota)
app.include_router(fontes.rota)
app.include_router(eventos.rota)
app.include_router(posicoes.rota)
app.include_router(series.rota)
app.include_router(previsao.rota)
app.include_router(radar.rota)
app.include_router(locais.rota)
app.include_router(chuva.rota)
app.include_router(mobilidade.rota)
app.include_router(transito.rota)
app.include_router(seguranca.rota)
app.include_router(ar.rota)
