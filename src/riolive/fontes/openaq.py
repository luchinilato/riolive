"""Qualidade do ar via OpenAQ v3 (substitui o MonitorAr, morto).

28 estações num raio de 25 km do centro (validado 2026-08-06 e 2026-08-05 com a
key do Luciano), 24 com leitura da própria hora: PM10/PM2.5 em todas, O3/NO2/CO
em várias. Dado horário; uma chamada de descoberta + uma de `latest` por estação
(29 req/rodada, folgado no rate limit free de 60/min).

Chave no `.env` (RIOLIVE_OPENAQ_API_KEY), header X-API-Key. Chave ausente é
defeito de configuração NOSSO: estoura RuntimeError e o run falha no Dagster
(não vira estado de saúde da fonte).
"""

from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel

from riolive.config import config
from riolive.ingestao.contrato import (
    ErroSchema,
    FonteConfig,
    LocalNovo,
    MedicaoNova,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp

URL_BASE = "https://api.openaq.org/v3"
CENTRO = "-22.91,-43.2"
RAIO_M = "25000"  # máximo da API; cobre o município

# parâmetro OpenAQ → vocabulário controlado de `metrica` (demais sensores são ignorados)
METRICAS_OPENAQ = {
    "pm25": "pm25",
    "pm10": "pm10",
    "o3": "o3",
    "no2": "no2",
    "co": "co",
    "so2": "so2",
}


class SensorOpenAq(BaseModel):
    id: int
    parametro: str
    unidades: str


class EstacaoOpenAq(BaseModel):
    """Schema de um resultado de /v3/locations."""

    id: int
    nome: str
    lat: float
    lon: float
    sensores: list[SensorOpenAq]


def _cabecalhos() -> dict[str, str]:
    chave = config().openaq_api_key.get_secret_value()
    if not chave:
        raise RuntimeError("RIOLIVE_OPENAQ_API_KEY não configurada no .env")
    return {"X-API-Key": chave}


def _interpretar_estacao(bruto: dict[str, Any]) -> EstacaoOpenAq:
    coordenadas = bruto.get("coordinates") or {}
    return EstacaoOpenAq(
        id=bruto["id"],
        nome=str(bruto.get("name") or f"OpenAQ {bruto['id']}").strip(),
        lat=coordenadas["latitude"],
        lon=coordenadas["longitude"],
        sensores=[
            SensorOpenAq(
                id=s["id"],
                parametro=s["parameter"]["name"],
                unidades=s["parameter"]["units"],
            )
            for s in bruto.get("sensors", [])
        ],
    )


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    cabecalhos = _cabecalhos()
    resposta = cliente.obter(
        f"{URL_BASE}/locations",
        params={"coordinates": CENTRO, "radius": RAIO_M, "limit": "100"},
        headers=cabecalhos,
    )
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} no /locations do OpenAQ")
    resultados = resposta.json().get("results")
    if not resultados:
        raise ErroSchema("OpenAQ sem estações no raio — resposta quebrada?")

    locais: list[LocalNovo] = []
    medicoes: list[MedicaoNova] = []
    marca_frescor: datetime | None = None

    for bruto in resultados:
        estacao = _interpretar_estacao(bruto)
        mapa_sensores = {
            s.id: (METRICAS_OPENAQ[s.parametro], s.unidades)
            for s in estacao.sensores
            if s.parametro in METRICAS_OPENAQ
        }
        if not mapa_sensores:
            continue  # estação só com sensores fora do nosso vocabulário
        locais.append(
            LocalNovo(
                codigo_externo=str(estacao.id),
                nome=estacao.nome,
                tipo="estacao_ar",
                lat=estacao.lat,
                lon=estacao.lon,
            )
        )
        ultimas = cliente.obter(f"{URL_BASE}/locations/{estacao.id}/latest", headers=cabecalhos)
        if ultimas.status_code != 200:
            raise ErroSchema(f"HTTP {ultimas.status_code} no /latest da estação {estacao.id}")
        for leitura in ultimas.json().get("results", []):
            sensor = mapa_sensores.get(leitura["sensorsId"])
            if sensor is None:
                continue
            metrica, unidades = sensor
            ts = datetime.fromisoformat(leitura["datetime"]["utc"])
            marca_frescor = max(marca_frescor, ts) if marca_frescor else ts
            medicoes.append(
                MedicaoNova(
                    codigo_local=str(estacao.id),
                    metrica=metrica,
                    ts=ts,
                    valor=leitura["value"],
                    payload={"unidades": unidades},
                )
            )

    return ResultadoColeta(medicoes=medicoes, locais=locais, marca_frescor=marca_frescor)


FONTE = FonteConfig(
    slug="openaq",
    nome="Qualidade do ar (OpenAQ)",
    orgao="OpenAQ (agregando SMAC/INEA e outros)",
    url=URL_BASE,
    bloco="D",
    criticidade=3,
    cadencia=timedelta(minutes=30),  # dado é horário; 30 min limita o atraso de captura
    tolerancia_frescor=timedelta(hours=3),
    coletar=coletar,
    licenca="CC-BY 4.0",
)
