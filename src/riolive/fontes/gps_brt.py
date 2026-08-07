"""GPS da frota BRT (dados.mobilidade.rio).

Formato distinto do SPPO (por isso parser separado): snapshot sem parâmetros,
wrapper {"veiculos": [...]}, floats com ponto, epoch ms, e campos ricos —
sentido, trajeto, direção, ignição, capacidades — que vão pro `extra`.
"""

import json
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, field_validator

from riolive.fontes.comum import coordenada_plausivel
from riolive.ingestao.contrato import (
    ErroSchema,
    FonteConfig,
    PosicaoNova,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp

URL = "https://dados.mobilidade.rio/gps/brt"


class RegistroBrt(BaseModel):
    """Schema de um veículo do payload do BRT."""

    codigo: str
    latitude: float
    longitude: float
    dataHora: datetime
    velocidade: float
    linha: str | None = None
    sentido: str | None = None
    trajeto: str | None = None
    ignicao: int | None = None

    @field_validator("dataHora", mode="before")
    @classmethod
    def _epoch_ms_utc(cls, bruto: object) -> object:
        if isinstance(bruto, str | int | float):
            return datetime.fromtimestamp(int(bruto) / 1000, tz=UTC)
        return bruto


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    resposta = cliente.obter(URL)
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} no GPS BRT")
    try:
        corpo = resposta.json()
    except json.JSONDecodeError as exc:
        raise ErroSchema(f"resposta não é JSON: {exc}") from exc
    veiculos = corpo.get("veiculos")
    if not isinstance(veiculos, list):
        raise ErroSchema("payload sem a lista `veiculos`")

    posicoes: list[PosicaoNova] = []
    marca_frescor: datetime | None = None
    for bruto in veiculos:
        registro = RegistroBrt.model_validate(bruto)
        if not coordenada_plausivel(registro.latitude, registro.longitude):
            continue
        marca_frescor = (
            max(marca_frescor, registro.dataHora) if marca_frescor else registro.dataHora
        )
        posicoes.append(
            PosicaoNova(
                modal="brt",
                veiculo_id=registro.codigo,
                ts=registro.dataHora,
                lat=registro.latitude,
                lon=registro.longitude,
                linha=registro.linha,
                velocidade=round(registro.velocidade),
                extra={
                    "sentido": registro.sentido,
                    "trajeto": registro.trajeto,
                    "ignicao": registro.ignicao,
                },
            )
        )

    return ResultadoColeta(posicoes=posicoes, marca_frescor=marca_frescor)


FONTE = FonteConfig(
    slug="gps_brt",
    nome="GPS da frota BRT",
    orgao="SMTR / Prefeitura do Rio",
    url=URL,
    bloco="B",
    criticidade=4,
    cadencia=timedelta(minutes=1),
    tolerancia_frescor=timedelta(minutes=10),
    coletar=coletar,
)
