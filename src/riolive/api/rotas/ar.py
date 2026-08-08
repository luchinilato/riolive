"""GET /ar/estacoes — última leitura de poluentes por estação (card e dossiê do Ar).

Espelha `/chuva/estacoes`. A janela é maior porque o OpenAQ publica a cada 30 min
e estação que atrasa uma rodada não deve sumir da lista — sumir daria a impressão
de que a estação não existe, quando ela só está atrasada.
"""

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from riolive.api.zonas import FILTRO_SQL, ZonaQuery, valor
from riolive.db import sessao

rota = APIRouter(tags=["ar"])

POLUENTES = ("pm25", "pm10", "no2", "o3", "so2", "co")


@rota.get("/ar/estacoes")
def estacoes_ar(zona: ZonaQuery = None) -> list[dict[str, Any]]:
    with sessao() as s:
        linhas = s.execute(
            text(
                f"""
                SELECT l.id, l.nome, b.nome bairro, r.nome ra, r.zona,
                       ST_Y(l.geom) lat, ST_X(l.geom) lon,
                       u.metrica, u.valor, u.ts
                FROM local l
                JOIN fonte f ON f.id = l.fonte_id AND f.slug = 'openaq'
                LEFT JOIN bairro b ON b.id = l.bairro_id
                LEFT JOIN ra r ON r.id = l.ra_id
                LEFT JOIN LATERAL (
                    SELECT DISTINCT ON (metrica) metrica, valor, ts FROM medicao
                    WHERE local_id = l.id
                      AND metrica = ANY(:poluentes)
                      AND ts > now() - interval '6 hours'
                    ORDER BY metrica, ts DESC
                ) u ON TRUE
                WHERE {FILTRO_SQL}
                ORDER BY l.id
                """
            ),
            {"poluentes": list(POLUENTES), "zona": valor(zona)},
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
                "zona": linha.zona,
                "lat": linha.lat,
                "lon": linha.lon,
                "leituras": {},
                "ts": None,
            },
        )
        if linha.metrica:
            est["leituras"][linha.metrica] = linha.valor
            est["ts"] = max(est["ts"], linha.ts) if est["ts"] else linha.ts
    return [
        {**est, "ts": est["ts"].isoformat() if est["ts"] else None} for est in por_estacao.values()
    ]
