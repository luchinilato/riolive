"""GET /eventos — eventos com filtros de recorte. Lê SÓ a vw_evento_publico."""

from typing import Annotated, Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from riolive.api.zonas import ZonaQuery, valor
from riolive.db import sessao

rota = APIRouter(tags=["eventos"])


@rota.get("/eventos")
def listar_eventos(
    tipo: str | None = None,
    bairro_id: int | None = None,
    ra_id: int | None = None,
    zona: ZonaQuery = None,
    severidade_min: Annotated[int, Query(ge=1, le=5)] = 1,
    horas: Annotated[int, Query(ge=1, le=24 * 30)] = 24,
    vigentes: bool = False,
    limite: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[dict[str, Any]]:
    # Condições qualificadas com `v.`: o join com bairro/ra traz `ra_id` e `nome`
    # homônimos, e coluna ambígua aqui seria erro de SQL em tempo de execução.
    condicoes = ["(v.fim IS NULL OR v.inicio > now() - make_interval(hours => :horas))"]
    parametros: dict[str, Any] = {"horas": horas, "severidade_min": severidade_min, "lim": limite}
    condicoes.append("v.severidade >= :severidade_min")
    if tipo:
        condicoes.append("v.tipo = :tipo")
        parametros["tipo"] = tipo
    if bairro_id is not None:
        condicoes.append("v.bairro_id = :bairro_id")
        parametros["bairro_id"] = bairro_id
    if ra_id is not None:
        condicoes.append("v.ra_id = :ra_id")
        parametros["ra_id"] = ra_id
    if zona is not None:
        # Evento sem RA sai do recorte, e isso inclui o que vale para a cidade
        # inteira: o estágio do COR não pertence a zona nenhuma. Quem pede uma
        # zona está perguntando "o que aconteceu AQUI", não "o que vale aqui".
        condicoes.append("r.zona = :zona")
        parametros["zona"] = valor(zona)
    if vigentes:
        condicoes.append("v.fim IS NULL")
    # O nome do bairro vem junto de propósito: sem ele o consumidor cai no título do
    # evento pra dizer "onde", e título de foco de calor é o nome do satélite.
    with sessao() as s:
        linhas = s.execute(
            text(
                "SELECT v.id, v.tipo, v.fonte_id, v.severidade, v.inicio, v.fim, v.titulo, "
                "v.descricao, ST_Y(v.geom) lat, ST_X(v.geom) lon, v.bairro_id, v.ra_id, v.h3_r8, "
                "b.nome AS bairro, r.nome AS ra, r.zona, e.payload->'llm' AS llm "
                "FROM vw_evento_publico v "
                "JOIN evento e ON e.id = v.id "
                "LEFT JOIN bairro b ON b.id = v.bairro_id "
                "LEFT JOIN ra r ON r.id = v.ra_id "
                f"WHERE {' AND '.join(condicoes)} "
                "ORDER BY v.inicio DESC LIMIT :lim"
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
            "bairro": linha.bairro,
            "ra_id": linha.ra_id,
            "ra": linha.ra,
            "zona": linha.zona,
            "h3_r8": linha.h3_r8,
            # Extração de texto por modelo de linguagem, quando existe: relato,
            # não medição. Vem embaixo de `llm` e rotulado, pra que o consumidor
            # nunca confunda com o que a fonte publicou.
            "llm": linha.llm,
        }
        for linha in linhas
    ]
