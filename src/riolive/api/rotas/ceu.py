"""GET /ceu/aeronaves — o que está voando sobre a região, pro dossiê do Céu.

O `/posicoes` serve o mapa e não expõe o `extra` da posição; aqui a altitude
importa, porque é ela que separa quem está em rota de quem está pousando. O que
NÃO temos é plano de voo: sem isso não dá pra dizer pouso, decolagem nem
aeroporto de destino, e o dossiê declara isso em vez de inventar.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["ceu"])

# adsb.lol devolve altitude barométrica em pés; "ground" quando a aeronave está no solo
ALTITUDE_BAIXA_PES = 5000


def _altitude(bruto: Any) -> int | None:
    if isinstance(bruto, int | float):
        return int(bruto)
    return None  # "ground" ou ausente: não é número, não vira número


@rota.get("/ceu/aeronaves")
def aeronaves(
    minutos: Annotated[int, Query(ge=1, le=60)] = 10,
    horas: Annotated[int, Query(ge=1, le=24 * 7)] = 24,
) -> dict[str, Any]:
    with sessao() as s:
        atuais = s.execute(
            text(
                "SELECT DISTINCT ON (veiculo_id) veiculo_id, linha, "
                "  ST_Y(geom) lat, ST_X(geom) lon, velocidade, ts, extra "
                "FROM posicao WHERE modal = 'aviao' "
                "  AND ts > now() - make_interval(mins => :minutos) "
                "ORDER BY veiculo_id, ts DESC"
            ),
            {"minutos": minutos},
        ).all()
        serie = s.execute(
            text(
                "SELECT bucket, count(*) AS aeronaves FROM frota_veiculo_15min "
                "WHERE modal = 'aviao' AND bucket > now() - make_interval(hours => :horas) "
                "GROUP BY bucket ORDER BY bucket"
            ),
            {"horas": horas},
        ).all()

    lista = [
        {
            "veiculo": linha.veiculo_id,
            "voo": linha.linha,
            "lat": linha.lat,
            "lon": linha.lon,
            "velocidade_kmh": linha.velocidade,
            "altitude_pes": _altitude((linha.extra or {}).get("alt_baro")),
            "no_solo": (linha.extra or {}).get("alt_baro") == "ground",
            "categoria": (linha.extra or {}).get("categoria"),
            "ts": linha.ts.isoformat(),
        }
        for linha in atuais
    ]
    baixas = [
        a for a in lista if a["altitude_pes"] is not None and a["altitude_pes"] < ALTITUDE_BAIXA_PES
    ]
    return {
        "minutos": minutos,
        "aeronaves": lista,
        "total": len(lista),
        "em_altitude_baixa": len(baixas),
        "limite_altitude_baixa_pes": ALTITUDE_BAIXA_PES,
        "serie_15min": [
            {"ts": linha.bucket.isoformat(), "aeronaves": linha.aeronaves} for linha in serie
        ],
    }
