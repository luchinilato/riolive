"""GET /eventos — eventos com filtros de recorte. Lê SÓ a vw_evento_publico."""

from typing import Annotated, Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["eventos"])


@rota.get("/eventos")
def listar_eventos(
    tipo: str | None = None,
    bairro_id: int | None = None,
    ra_id: int | None = None,
    severidade_min: Annotated[int, Query(ge=1, le=5)] = 1,
    horas: Annotated[int, Query(ge=1, le=24 * 30)] = 24,
    vigentes: bool = False,
    limite: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[dict[str, Any]]:
    condicoes = ["(fim IS NULL OR inicio > now() - make_interval(hours => :horas))"]
    parametros: dict[str, Any] = {"horas": horas, "severidade_min": severidade_min, "lim": limite}
    condicoes.append("severidade >= :severidade_min")
    if tipo:
        condicoes.append("tipo = :tipo")
        parametros["tipo"] = tipo
    if bairro_id is not None:
        condicoes.append("bairro_id = :bairro_id")
        parametros["bairro_id"] = bairro_id
    if ra_id is not None:
        condicoes.append("ra_id = :ra_id")
        parametros["ra_id"] = ra_id
    if vigentes:
        condicoes.append("fim IS NULL")
    with sessao() as s:
        linhas = s.execute(
            text(
                "SELECT id, tipo, fonte_id, severidade, inicio, fim, titulo, descricao, "
                "ST_Y(geom) lat, ST_X(geom) lon, bairro_id, ra_id, h3_r8 "
                f"FROM vw_evento_publico WHERE {' AND '.join(condicoes)} "
                "ORDER BY inicio DESC LIMIT :lim"
            ),
            parametros,
        ).all()
    return [
        {
            "id": str(linha.id),
            "tipo": linha.tipo,
            "severidade": linha.severidade,
            "inicio": linha.inicio.isoformat(),
            "fim": linha.fim.isoformat() if linha.fim else None,
            "titulo": linha.titulo,
            "descricao": linha.descricao,
            "lat": linha.lat,
            "lon": linha.lon,
            "bairro_id": linha.bairro_id,
            "ra_id": linha.ra_id,
            "h3_r8": linha.h3_r8,
        }
        for linha in linhas
    ]
