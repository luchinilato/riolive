"""GET /previsao — rodada mais recente por instante-alvo (vw_previsao_atual)."""

from typing import Annotated, Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["previsao"])


@rota.get("/previsao")
def previsao(
    local: str = "centro",
    metrica: str | None = None,
    horas: Annotated[int, Query(ge=1, le=72)] = 24,
) -> dict[str, Any]:
    parametros: dict[str, Any] = {"local": local, "horas": horas}
    filtro_metrica = ""
    if metrica:
        filtro_metrica = "AND v.metrica = :metrica"
        parametros["metrica"] = metrica
    with sessao() as s:
        linhas = s.execute(
            text(
                "SELECT v.metrica, v.ts_alvo, v.valor, v.emitida_em "
                "FROM vw_previsao_atual v JOIN local l ON l.id = v.local_id "
                f"WHERE l.codigo_externo = :local {filtro_metrica} "
                "AND v.ts_alvo BETWEEN now() AND now() + make_interval(hours => :horas) "
                "ORDER BY v.metrica, v.ts_alvo"
            ),
            parametros,
        ).all()
    por_metrica: dict[str, list[dict[str, Any]]] = {}
    emitida = None
    for linha in linhas:
        emitida = max(emitida, linha.emitida_em) if emitida else linha.emitida_em
        por_metrica.setdefault(linha.metrica, []).append(
            {"ts": linha.ts_alvo.isoformat(), "valor": linha.valor}
        )
    return {
        "local": local,
        "emitida_em": emitida.isoformat() if emitida else None,
        "metricas": por_metrica,
    }
