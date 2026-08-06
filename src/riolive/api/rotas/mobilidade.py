"""GET /mobilidade/linhas — planejado × realizado por linha (Tese 3), pro dossiê."""

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from riolive.db import sessao
from riolive.mobilidade import detectar_paradas, gps_saudavel, linhas_agora, resumo

rota = APIRouter(tags=["mobilidade"])


@rota.get("/mobilidade/linhas")
def planejado_realizado() -> dict[str, Any]:
    with sessao() as s:
        linhas = linhas_agora(s)
        saudavel = gps_saudavel(s)
        paradas = detectar_paradas(linhas) if saudavel else []
        serie = s.execute(
            text(
                "SELECT bucket, count(*) AS veiculos FROM frota_veiculo_15min "
                "WHERE bucket > now() - interval '24 hours' "
                "GROUP BY bucket ORDER BY bucket"
            )
        ).all()
    return {
        "gps_saudavel": saudavel,
        **resumo(linhas),
        "linhas_paradas": [
            {"linha": p.linha, "nome": p.nome, "minutos_sem_gps": p.minutos_sem_gps}
            for p in paradas
        ],
        "linhas": [
            {
                "linha": li.linha,
                "nome": li.nome,
                "headway_min": round(li.headway_seg / 60),
                "veiculos": li.veiculos,
                "minutos_sem_gps": li.minutos_sem_gps,
            }
            for li in linhas
        ],
        "serie_veiculos_15min": [
            {"ts": b.bucket.isoformat(), "veiculos": b.veiculos} for b in serie
        ],
    }
