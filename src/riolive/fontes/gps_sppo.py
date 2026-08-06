"""GPS da frota de ônibus SPPO (dados.mobilidade.rio).

Pegadinhas (catálogo, confirmadas ao vivo em 2026-08-06):
- Params dataInicial/dataFinal são OBRIGATÓRIOS e em hora local do Rio.
- `datahora` é epoch em milissegundos UTC; `latitude`/`longitude` são strings
  com vírgula decimal; `velocidade` é string.
- Janelas de coleta se sobrepõem: dedup na PK (modal, veiculo_id, ts).
~15.5k registros a cada 2 min; fonte quente (cadência 1 min, job agregador).
"""

import json
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, field_validator

from riolive.fontes.comum import TZ_RIO, coordenada_plausivel
from riolive.ingestao.contrato import (
    ErroSchema,
    FonteConfig,
    PosicaoNova,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp

URL = "https://dados.mobilidade.rio/gps/sppo"
JANELA = timedelta(minutes=3)  # sobrepõe a cadência de 1 min de propósito


class RegistroSppo(BaseModel):
    """Schema de um registro do payload do SPPO."""

    ordem: str
    latitude: float
    longitude: float
    datahora: datetime
    velocidade: int
    linha: str

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def _virgula_decimal(cls, bruto: object) -> object:
        if isinstance(bruto, str):
            return bruto.replace(",", ".")
        return bruto

    @field_validator("datahora", mode="before")
    @classmethod
    def _epoch_ms_utc(cls, bruto: object) -> object:
        if isinstance(bruto, str | int | float):
            return datetime.fromtimestamp(int(bruto) / 1000, tz=UTC)
        return bruto

    @field_validator("velocidade", mode="before")
    @classmethod
    def _velocidade_int(cls, bruto: object) -> object:
        if isinstance(bruto, str):
            return int(float(bruto.replace(",", ".")))
        return bruto


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    fim = datetime.now(tz=TZ_RIO)
    inicio = fim - JANELA
    formato = "%Y-%m-%d %H:%M:%S"
    resposta = cliente.obter(
        URL,
        params={"dataInicial": inicio.strftime(formato), "dataFinal": fim.strftime(formato)},
    )
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} no GPS SPPO")
    try:
        registros = resposta.json()
    except json.JSONDecodeError as exc:
        raise ErroSchema(f"resposta não é JSON: {exc}") from exc
    if not isinstance(registros, list):
        raise ErroSchema(f"esperava lista, veio {type(registros).__name__}")

    posicoes: list[PosicaoNova] = []
    marca_frescor: datetime | None = None
    for bruto in registros:
        registro = RegistroSppo.model_validate(bruto)
        # Coordenada fora da região metropolitana = glitch de GPS; descarta o ponto
        if not coordenada_plausivel(registro.latitude, registro.longitude):
            continue
        marca_frescor = (
            max(marca_frescor, registro.datahora) if marca_frescor else registro.datahora
        )
        posicoes.append(
            PosicaoNova(
                modal="onibus",
                veiculo_id=registro.ordem,
                ts=registro.datahora,
                lat=registro.latitude,
                lon=registro.longitude,
                linha=registro.linha,
                velocidade=registro.velocidade,
            )
        )

    return ResultadoColeta(posicoes=posicoes, marca_frescor=marca_frescor)


FONTE = FonteConfig(
    slug="gps_sppo",
    nome="GPS da frota SPPO (ônibus)",
    orgao="SMTR / Prefeitura do Rio",
    url=URL,
    bloco="B",
    criticidade=4,
    cadencia=timedelta(minutes=1),
    tolerancia_frescor=timedelta(minutes=10),
    coletar=coletar,
)
