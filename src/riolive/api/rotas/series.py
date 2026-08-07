"""GET /series/{metrica} — séries temporais (a Tese 2 servida como API).

Passo bruto lê a hypertable; 1h/1d leem os agregados contínuos — consulta
histórica nunca toca o dado cru.
"""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from riolive.db import sessao
from riolive.modelos import METRICAS

rota = APIRouter(tags=["series"])


@rota.get("/series/{metrica}")
def serie(
    metrica: str,
    local_id: int | None = None,
    passo: Literal["bruto", "1h", "1d"] = "1h",
    horas: Annotated[int, Query(ge=1, le=24 * 365)] = 24,
) -> dict[str, Any]:
    if metrica not in METRICAS:
        raise HTTPException(404, f"métrica desconhecida: {metrica}")
    parametros: dict[str, Any] = {"metrica": metrica, "horas": horas}
    filtro_local = ""
    if local_id is not None:
        filtro_local = "AND local_id = :local_id"
        parametros["local_id"] = local_id

    if passo == "bruto":
        sql = (
            "SELECT ts, local_id, valor FROM medicao "
            f"WHERE metrica = :metrica {filtro_local} "
            "AND ts > now() - make_interval(hours => :horas) ORDER BY ts"
        )
    else:
        tabela = "medicao_1h" if passo == "1h" else "medicao_1d"
        sql = (
            f"SELECT bucket ts, local_id, media, minimo, maximo, n FROM {tabela} "
            f"WHERE metrica = :metrica {filtro_local} "
            "AND bucket > now() - make_interval(hours => :horas) ORDER BY bucket"
        )
    with sessao() as s:
        linhas = s.execute(text(sql), parametros).mappings().all()
    pontos = [
        {chave: (valor.isoformat() if chave == "ts" else valor) for chave, valor in linha.items()}
        for linha in linhas
    ]
    return {"metrica": metrica, "passo": passo, "pontos": pontos}
