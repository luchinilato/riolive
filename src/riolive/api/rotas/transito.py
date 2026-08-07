"""GET /transito/corredores — última leitura TomTom por corredor + série 24 h."""

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["transito"])


@rota.get("/transito/corredores")
def corredores() -> dict[str, Any]:
    with sessao() as s:
        linhas = s.execute(
            text(
                """
                SELECT l.codigo_externo, l.nome,
                       max(m.valor) FILTER (WHERE m.metrica = 'vel_kmh') AS agora,
                       max(m.valor) FILTER (WHERE m.metrica = 'vel_livre_kmh') AS livre,
                       max(m.ts) AS ts
                FROM medicao m
                JOIN local l ON l.id = m.local_id AND l.tipo = 'corredor'
                WHERE m.ts > now() - interval '2 hours'
                GROUP BY l.codigo_externo, l.nome
                """
            )
        ).all()
        serie = s.execute(
            text(
                "SELECT bucket, round(avg(media)) AS vel FROM medicao_1h "
                "WHERE metrica = 'vel_kmh' AND bucket > now() - interval '24 hours' "
                "GROUP BY bucket ORDER BY bucket"
            )
        ).all()

    corredores_saida = []
    for linha in linhas:
        fluidez = round(100 * linha.agora / linha.livre) if linha.agora and linha.livre else None
        corredores_saida.append(
            {
                "codigo": linha.codigo_externo,
                "nome": linha.nome,
                "agora_kmh": linha.agora,
                "livre_kmh": linha.livre,
                "fluidez_pct": fluidez,
                "ts": linha.ts.isoformat() if linha.ts else None,
            }
        )
    corredores_saida.sort(key=lambda c: c["fluidez_pct"] if c["fluidez_pct"] is not None else 999)
    com_dado = [c for c in corredores_saida if c["agora_kmh"]]
    return {
        "corredores": corredores_saida,
        "media_kmh": round(sum(c["agora_kmh"] for c in com_dado) / len(com_dado))
        if com_dado
        else None,
        "media_livre_kmh": round(sum(c["livre_kmh"] for c in com_dado) / len(com_dado))
        if com_dado
        else None,
        "congestionados": sum(1 for c in com_dado if (c["fluidez_pct"] or 100) < 60),
        "serie_24h": [{"ts": b.bucket.isoformat(), "vel": b.vel} for b in serie],
    }
