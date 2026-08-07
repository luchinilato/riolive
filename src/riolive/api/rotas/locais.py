"""GET /locais — pontos fixos (estações) com geo e enriquecimento, pros mapas do painel."""

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["locais"])


@rota.get("/locais")
def listar_locais(tipo: str | None = None, fonte: str | None = None) -> dict[str, Any]:
    condicoes = ["TRUE"]
    parametros: dict[str, Any] = {}
    if tipo:
        condicoes.append("l.tipo = :tipo")
        parametros["tipo"] = tipo
    if fonte:
        condicoes.append("f.slug = :fonte")
        parametros["fonte"] = fonte
    with sessao() as s:
        linhas = s.execute(
            text(
                "SELECT l.id, l.codigo_externo, l.nome, l.tipo, f.slug fonte, "
                "ST_Y(l.geom) lat, ST_X(l.geom) lon, l.bairro_id, b.nome bairro, l.h3_r8 "
                "FROM local l JOIN fonte f ON f.id = l.fonte_id "
                "LEFT JOIN bairro b ON b.id = l.bairro_id "
                f"WHERE {' AND '.join(condicoes)} ORDER BY l.id"
            ),
            parametros,
        ).all()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [linha.lon, linha.lat]},
                "properties": {
                    "id": linha.id,
                    "codigo": linha.codigo_externo,
                    "nome": linha.nome,
                    "tipo": linha.tipo,
                    "fonte": linha.fonte,
                    "bairro": linha.bairro,
                    "h3_r8": linha.h3_r8,
                },
            }
            for linha in linhas
        ],
    }
