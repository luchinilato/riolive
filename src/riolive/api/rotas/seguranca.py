"""GET /seguranca/resumo — dossiê de segurança sobre a base do Fogo Cruzado.

O histórico completo (2016+) é o material mais denso do banco, e o dossiê é onde
ele aparece: recorte recente com contexto de longo prazo do lado.

Salvaguardas da [[DEC - Exibição de segurança sem salvaguardas de borrão e atraso]]:
pino exato, sem atraso. Aqui não há pino — este endpoint é agregado; o mapa
consome `/eventos`, que já lê só a `vw_evento_publico`. Mortos e feridos saem do
payload do Fogo Cruzado e são somados como vieram, sem reinterpretação.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from riolive.api.zonas import FILTRO_SQL, ZonaQuery, valor
from riolive.db import sessao

rota = APIRouter(tags=["seguranca"])

# Janela curta pede granularidade de hora; a longa viraria um gráfico ilegível.
PASSO_POR_JANELA = {24: "hour", 24 * 7: "day", 24 * 30: "day"}

# O recorte precisa valer também no `por_ano`. Ele é a memória da cidade e não
# depende da janela — mas depende do território: zona de hoje contra história da
# cidade inteira é a mesma comparação torta que a climatologia evita.
#
# `LEFT JOIN`, não `JOIN`: 5 dos 28.612 tiroteios não têm RA resolvida, e sem
# zona pedida eles têm que continuar contando. O recorte fica no WHERE, onde
# some com eles só quando alguém pediu uma zona.
JUNCAO_ZONA = "LEFT JOIN ra r ON r.id = e.ra_id"


@rota.get("/seguranca/resumo")
def resumo_seguranca(
    horas: Annotated[int, Query(ge=1, le=24 * 365)] = 24,
    limite_bairros: Annotated[int, Query(ge=1, le=50)] = 10,
    zona: ZonaQuery = None,
) -> dict[str, Any]:
    passo = PASSO_POR_JANELA.get(horas, "month" if horas > 24 * 90 else "day")
    parametros = {"horas": horas, "lim": limite_bairros, "zona": valor(zona)}

    with sessao() as s:
        kpis = s.execute(
            text(
                "SELECT count(*) AS ocorrencias, "
                "  coalesce(sum((e.payload->>'mortos')::int), 0) AS mortos, "
                "  coalesce(sum((e.payload->>'feridos')::int), 0) AS feridos, "
                "  count(*) FILTER (WHERE (e.payload->>'acao_policial')::bool) AS acao_policial "
                f"FROM evento e {JUNCAO_ZONA} WHERE e.tipo = 'tiroteio' "
                "  AND e.inicio > now() - make_interval(hours => :horas) "
                f"  AND {FILTRO_SQL}"
            ),
            parametros,
        ).one()

        serie = s.execute(
            text(
                f"SELECT date_trunc('{passo}', e.inicio) AS balde, count(*) AS ocorrencias, "
                "  coalesce(sum((e.payload->>'mortos')::int), 0) AS mortos "
                f"FROM evento e {JUNCAO_ZONA} WHERE e.tipo = 'tiroteio' "
                "  AND e.inicio > now() - make_interval(hours => :horas) "
                f"  AND {FILTRO_SQL} "
                "GROUP BY balde ORDER BY balde"
            ),
            parametros,
        ).all()

        bairros = s.execute(
            text(
                "SELECT b.nome, b.id AS bairro_id, count(*) AS ocorrencias, "
                "  coalesce(sum((e.payload->>'mortos')::int), 0) AS mortos "
                f"FROM evento e JOIN bairro b ON b.id = e.bairro_id {JUNCAO_ZONA} "
                "WHERE e.tipo = 'tiroteio' "
                "  AND e.inicio > now() - make_interval(hours => :horas) "
                f"  AND {FILTRO_SQL} "
                "GROUP BY b.id, b.nome ORDER BY ocorrencias DESC, b.nome LIMIT :lim"
            ),
            parametros,
        ).all()

        # Contexto de longo prazo: não depende da janela, é a memória da cidade
        anos = s.execute(
            text(
                "SELECT extract(year FROM e.inicio)::int AS ano, count(*) AS ocorrencias, "
                "  coalesce(sum((e.payload->>'mortos')::int), 0) AS mortos "
                f"FROM evento e {JUNCAO_ZONA} WHERE e.tipo = 'tiroteio' "
                f"  AND {FILTRO_SQL} "
                "GROUP BY ano ORDER BY ano"
            ),
            parametros,
        ).all()

    return {
        "horas": horas,
        "passo": passo,
        "zona": valor(zona),
        "ocorrencias": kpis.ocorrencias,
        "mortos": kpis.mortos,
        "feridos": kpis.feridos,
        "acao_policial": kpis.acao_policial,
        "serie": [
            {
                "ts": linha.balde.isoformat(),
                "ocorrencias": linha.ocorrencias,
                "mortos": linha.mortos,
            }
            for linha in serie
        ],
        "bairros": [
            {
                "bairro_id": linha.bairro_id,
                "nome": linha.nome,
                "ocorrencias": linha.ocorrencias,
                "mortos": linha.mortos,
            }
            for linha in bairros
        ],
        "por_ano": [
            {"ano": linha.ano, "ocorrencias": linha.ocorrencias, "mortos": linha.mortos}
            for linha in anos
        ],
    }
