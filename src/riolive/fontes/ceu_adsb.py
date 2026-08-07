"""Aeronaves sobre a região via adsb.lol (ODbL, sem auth).

API por ponto+raio (milhas náuticas). Campo `seen` = segundos desde a última
mensagem — posição velha (>60 s) é descartada, como manda o catálogo.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel

from riolive.ingestao.contrato import ErroSchema, FonteConfig, PosicaoNova, ResultadoColeta
from riolive.ingestao.fetcher import ClienteHttp

URL = "https://api.adsb.lol/v2/lat/-22.9/lon/-43.2/dist/40"
SEEN_MAX_S = 60
KT_PARA_KMH = 1.852


class Aeronave(BaseModel):
    hex: str
    lat: float
    lon: float
    flight: str | None = None
    gs: float | None = None  # ground speed em nós
    alt_baro: float | str | None = None  # pés, ou "ground"
    category: str | None = None
    seen: float = 0.0


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    resposta = cliente.obter(URL)
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} no adsb.lol")
    corpo: dict[str, Any] = resposta.json()
    if "ac" not in corpo:
        raise ErroSchema("resposta sem a lista `ac`")

    agora = datetime.now(tz=UTC)
    posicoes: list[PosicaoNova] = []
    marca_frescor: datetime | None = None
    for bruto in corpo["ac"] or []:
        if "lat" not in bruto or "lon" not in bruto:
            continue  # aeronave sem posição ADS-B nesta amostra
        aeronave = Aeronave.model_validate(bruto)
        if aeronave.seen > SEEN_MAX_S:
            continue
        ts = agora - timedelta(seconds=aeronave.seen)
        marca_frescor = max(marca_frescor, ts) if marca_frescor else ts
        posicoes.append(
            PosicaoNova(
                modal="aviao",
                veiculo_id=aeronave.hex,
                ts=ts,
                lat=aeronave.lat,
                lon=aeronave.lon,
                linha=(aeronave.flight or "").strip() or None,
                velocidade=round(aeronave.gs * KT_PARA_KMH) if aeronave.gs else None,
                extra={"alt_baro": aeronave.alt_baro, "categoria": aeronave.category},
            )
        )
    # céu vazio é possível de madrugada; frescor cobre a fonte, não o movimento
    return ResultadoColeta(posicoes=posicoes, marca_frescor=marca_frescor or agora)


FONTE = FonteConfig(
    slug="ceu_adsb",
    nome="Aeronaves sobre a região (adsb.lol)",
    orgao="adsb.lol (comunidade ADS-B)",
    url=URL,
    bloco="B",
    criticidade=2,
    cadencia=timedelta(minutes=1),
    tolerancia_frescor=timedelta(minutes=15),
    coletar=coletar,
    licenca="ODbL",
)
