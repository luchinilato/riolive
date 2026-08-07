"""GET /queimadas/resumo — focos de calor do INPE na janela, pro dossiê.

Foco de calor é detecção de satélite, não incêndio confirmado: o mesmo fogo pode
aparecer em duas passagens e um telhado quente pode virar foco. O endpoint devolve
o número cru e o `desde` da nossa série — a memória aqui é curta (a coleta começou
em 2026-08), e dizer isso é parte do dado.

O pino sai da `vw_evento_publico` (salvaguarda de esquema); o `payload` vem do
join com `evento` só pelo satélite, que a view não carrega.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["queimadas"])

PASSO_POR_JANELA = {24: "hour", 24 * 7: "day", 24 * 30: "day"}


@rota.get("/queimadas/resumo")
def resumo_queimadas(
    horas: Annotated[int, Query(ge=1, le=24 * 365)] = 24,
    limite_focos: Annotated[int, Query(ge=1, le=500)] = 100,
) -> dict[str, Any]:
    passo = PASSO_POR_JANELA.get(horas, "month" if horas > 24 * 90 else "day")
    parametros = {"horas": horas, "lim": limite_focos}

    with sessao() as s:
        kpis = s.execute(
            text(
                "SELECT count(*) AS focos, count(DISTINCT bairro_id) AS bairros, "
                "  max(inicio) AS ultimo "
                "FROM vw_evento_publico WHERE tipo = 'foco_calor' "
                "  AND inicio > now() - make_interval(hours => :horas)"
            ),
            parametros,
        ).one()

        serie = s.execute(
            text(
                f"SELECT date_trunc('{passo}', inicio) AS balde, count(*) AS focos "
                "FROM vw_evento_publico WHERE tipo = 'foco_calor' "
                "  AND inicio > now() - make_interval(hours => :horas) "
                "GROUP BY balde ORDER BY balde"
            ),
            parametros,
        ).all()

        bairros = s.execute(
            text(
                "SELECT b.id AS bairro_id, b.nome, count(*) AS focos, max(v.inicio) AS ultimo "
                "FROM vw_evento_publico v JOIN bairro b ON b.id = v.bairro_id "
                "WHERE v.tipo = 'foco_calor' "
                "  AND v.inicio > now() - make_interval(hours => :horas) "
                "GROUP BY b.id, b.nome ORDER BY focos DESC, b.nome"
            ),
            parametros,
        ).all()

        focos = s.execute(
            text(
                "SELECT v.id, v.inicio, ST_Y(v.geom) lat, ST_X(v.geom) lon, "
                "  b.nome AS bairro, r.nome AS ra, e.payload->>'satelite' AS satelite "
                "FROM vw_evento_publico v "
                "JOIN evento e ON e.id = v.id "
                "LEFT JOIN bairro b ON b.id = v.bairro_id "
                "LEFT JOIN ra r ON r.id = v.ra_id "
                "WHERE v.tipo = 'foco_calor' "
                "  AND v.inicio > now() - make_interval(hours => :horas) "
                "ORDER BY v.inicio DESC LIMIT :lim"
            ),
            parametros,
        ).all()

        # Memória declarada: a série do INPE é recente e o dossiê não pode sugerir histórico
        desde = s.execute(
            text("SELECT min(inicio) FROM vw_evento_publico WHERE tipo = 'foco_calor'")
        ).scalar()

    return {
        "horas": horas,
        "passo": passo,
        "focos": kpis.focos,
        "bairros_atingidos": kpis.bairros,
        "ultimo": kpis.ultimo.isoformat() if kpis.ultimo else None,
        "desde": desde.isoformat() if desde else None,
        "serie": [{"ts": linha.balde.isoformat(), "focos": linha.focos} for linha in serie],
        "por_bairro": [
            {
                "bairro_id": linha.bairro_id,
                "nome": linha.nome,
                "focos": linha.focos,
                "ultimo": linha.ultimo.isoformat(),
            }
            for linha in bairros
        ],
        "lista": [
            {
                "id": str(linha.id),
                "inicio": linha.inicio.isoformat(),
                "lat": linha.lat,
                "lon": linha.lon,
                "bairro": linha.bairro,
                "ra": linha.ra,
                "satelite": linha.satelite,
            }
            for linha in focos
        ],
    }
