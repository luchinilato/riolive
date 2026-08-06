"""GET /chuva/estacoes — última leitura de chuva por estação (tabela do dossiê)."""

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["chuva"])

METRICAS_TABELA = ("chuva_15min", "chuva_1h", "chuva_24h")


@rota.get("/chuva/estacoes")
def estacoes_chuva() -> list[dict[str, Any]]:
    with sessao() as s:
        linhas = s.execute(
            text(
                """
                SELECT l.id, l.nome, b.nome bairro, r.nome ra,
                       ST_Y(l.geom) lat, ST_X(l.geom) lon,
                       u.metrica, u.valor, u.ts
                FROM local l
                JOIN fonte f ON f.id = l.fonte_id AND f.slug = 'alerta_rio'
                LEFT JOIN bairro b ON b.id = l.bairro_id
                LEFT JOIN ra r ON r.id = l.ra_id
                LEFT JOIN LATERAL (
                    SELECT metrica, valor, ts FROM medicao
                    WHERE local_id = l.id
                      AND metrica IN ('chuva_15min', 'chuva_1h', 'chuva_24h')
                      AND ts > now() - interval '3 hours'
                    ORDER BY ts DESC LIMIT 6
                ) u ON TRUE
                ORDER BY l.id
                """
            )
        ).all()
    por_estacao: dict[int, dict[str, Any]] = {}
    for linha in linhas:
        est = por_estacao.setdefault(
            linha.id,
            {
                "id": linha.id,
                "nome": linha.nome,
                "bairro": linha.bairro,
                "ra": linha.ra,
                "lat": linha.lat,
                "lon": linha.lon,
                "leituras": {},
                "ts": None,
            },
        )
        if linha.metrica and linha.metrica not in est["leituras"]:
            est["leituras"][linha.metrica] = linha.valor
            est["ts"] = max(est["ts"], linha.ts) if est["ts"] else linha.ts
    return [
        {**est, "ts": est["ts"].isoformat() if est["ts"] else None}
        for est in por_estacao.values()
    ]
