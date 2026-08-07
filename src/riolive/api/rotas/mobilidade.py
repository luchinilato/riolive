"""GET /mobilidade/linhas — planejado × realizado por linha (Tese 3), pro dossiê."""

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from riolive.db import sessao
from riolive.mobilidade import detectar_paradas, gps_confiavel, linhas_agora, resumo

rota = APIRouter(tags=["mobilidade"])


@rota.get("/mobilidade/linhas")
def planejado_realizado() -> dict[str, Any]:
    with sessao() as s:
        linhas = linhas_agora(s)
        saudavel, motivo = gps_confiavel(s)
        paradas = detectar_paradas(linhas) if saudavel else []
        serie = s.execute(
            text(
                # só transporte de superfície: o agregado guarda avião e navio também,
                # e contá-los aqui inflaria a "frota" que o dossiê rotula como ônibus+BRT
                "SELECT bucket, count(*) AS veiculos FROM frota_veiculo_15min "
                "WHERE modal IN ('onibus', 'brt') AND bucket > now() - interval '24 hours' "
                "GROUP BY bucket ORDER BY bucket"
            )
        ).all()
    return {
        "gps_saudavel": saudavel,
        "gps_motivo": motivo,
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
