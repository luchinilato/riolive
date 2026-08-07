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

from riolive.db import sessao

rota = APIRouter(tags=["seguranca"])

# Janela curta pede granularidade de hora; a longa viraria um gráfico ilegível.
PASSO_POR_JANELA = {24: "hour", 24 * 7: "day", 24 * 30: "day"}


@rota.get("/seguranca/resumo")
def resumo_seguranca(
    horas: Annotated[int, Query(ge=1, le=24 * 365)] = 24,
    limite_bairros: Annotated[int, Query(ge=1, le=50)] = 10,
) -> dict[str, Any]:
    passo = PASSO_POR_JANELA.get(horas, "month" if horas > 24 * 90 else "day")
    parametros = {"horas": horas, "lim": limite_bairros}

    with sessao() as s:
        kpis = s.execute(
            text(
                "SELECT count(*) AS ocorrencias, "
                "  coalesce(sum((payload->>'mortos')::int), 0) AS mortos, "
                "  coalesce(sum((payload->>'feridos')::int), 0) AS feridos, "
                "  count(*) FILTER (WHERE (payload->>'acao_policial')::bool) AS acao_policial "
                "FROM evento WHERE tipo = 'tiroteio' "
                "  AND inicio > now() - make_interval(hours => :horas)"
            ),
            parametros,
        ).one()

        serie = s.execute(
            text(
                f"SELECT date_trunc('{passo}', inicio) AS balde, count(*) AS ocorrencias, "
                "  coalesce(sum((payload->>'mortos')::int), 0) AS mortos "
                "FROM evento WHERE tipo = 'tiroteio' "
                "  AND inicio > now() - make_interval(hours => :horas) "
                "GROUP BY balde ORDER BY balde"
            ),
            parametros,
        ).all()

        bairros = s.execute(
            text(
                "SELECT b.nome, b.id AS bairro_id, count(*) AS ocorrencias, "
                "  coalesce(sum((e.payload->>'mortos')::int), 0) AS mortos "
                "FROM evento e JOIN bairro b ON b.id = e.bairro_id "
                "WHERE e.tipo = 'tiroteio' "
                "  AND e.inicio > now() - make_interval(hours => :horas) "
                "GROUP BY b.id, b.nome ORDER BY ocorrencias DESC, b.nome LIMIT :lim"
            ),
            parametros,
        ).all()

        # Contexto de longo prazo: não depende da janela, é a memória da cidade
        anos = s.execute(
            text(
                "SELECT extract(year FROM inicio)::int AS ano, count(*) AS ocorrencias, "
                "  coalesce(sum((payload->>'mortos')::int), 0) AS mortos "
                "FROM evento WHERE tipo = 'tiroteio' GROUP BY ano ORDER BY ano"
            )
        ).all()

    return {
        "horas": horas,
        "passo": passo,
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
