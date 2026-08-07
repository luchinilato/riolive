"""GET /posicoes — frota ao vivo em GeoJSON (última posição por veículo na janela)."""

from typing import Annotated, Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["posicoes"])


@rota.get("/posicoes")
def frota_ao_vivo(
    modal: Annotated[str | None, Query(pattern="^(onibus|brt|aviao|navio)$")] = None,
    linha: str | None = None,
    minutos: Annotated[int, Query(ge=1, le=60)] = 5,
    limite: Annotated[int, Query(ge=1, le=20000)] = 10000,
) -> dict[str, Any]:
    condicoes = ["ts > now() - make_interval(mins => :minutos)"]
    parametros: dict[str, Any] = {"minutos": minutos, "lim": limite}
    if modal:
        condicoes.append("modal = :modal")
        parametros["modal"] = modal
    if linha:
        condicoes.append("linha = :linha")
        parametros["linha"] = linha
    with sessao() as s:
        linhas = s.execute(
            text(
                "SELECT DISTINCT ON (modal, veiculo_id) modal, veiculo_id, linha, "
                "ST_Y(geom) lat, ST_X(geom) lon, velocidade, ts "
                f"FROM posicao WHERE {' AND '.join(condicoes)} "
                "ORDER BY modal, veiculo_id, ts DESC LIMIT :lim"
            ),
            parametros,
        ).all()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]},
                "properties": {
                    "modal": p.modal,
                    "veiculo": p.veiculo_id,
                    "linha": p.linha,
                    "velocidade": p.velocidade,
                    "ts": p.ts.isoformat(),
                },
            }
            for p in linhas
        ],
    }
