"""GPS da frota de ônibus SPPO (dados.mobilidade.rio).

A SMTR trocou o schema deste endpoint entre 2026-08-06 02:00 e 2026-08-07 00:49
(quebra pega ao vivo em produção). O formato antigo — `ordem`, `linha`, epoch em
ms, lat/lon como string com vírgula decimal — morreu de vez: até as janelas
passadas voltam no formato novo. O BRT, no mesmo host, não foi tocado.

O novo payload fala GTFS (`trip_id`, `shape_id`, `route_id`, `servico`), o que é
um upgrade pra nós: 97% dos `trip_id` casam com a `gtfs_trips` já carregada, então
o detector de linha parada pode ler a viagem da origem em vez de adivinhar.

Pegadinhas (confirmadas ao vivo em 2026-08-07):
- Params dataInicial/dataFinal seguem OBRIGATÓRIOS e em hora local do Rio (sem
  eles a API devolve HTTP 500); janelas passadas funcionam — dá pra fazer backfill.
- **O sufixo `Z` do `datetime` é mentira**: o valor é hora local do Rio. Conferido
  em 2026-08-07 — o `datetime` máximo (02:11:39Z) batia com o relógio local
  (02:11:46), não com o UTC real (05:11:46). Parseado ao pé da letra, todo ponto
  entra 3 h no passado; quem pegou foi a checagem de frescor da máquina de saúde.
  O schema antigo não tinha esse defeito (o epoch em ms era UTC de verdade).
- lat/lon já vêm float; `velocidade` é float sempre inteiro (km/h); `direcao` é o
  azimute em graus.
- `route_id` vem nulo em 100% dos registros hoje — por isso não é gravado.
- `sentido` é I/V/C e vem vazio em ~30% dos registros.
- Janelas de coleta se sobrepõem: dedup na PK (modal, veiculo_id, ts).
~20k registros por janela de 3 min; fonte quente (cadência 1 min, job agregador).
"""

import json
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field, field_validator

from riolive.fontes.comum import TZ_RIO, coordenada_plausivel
from riolive.ingestao.contrato import (
    ErroSchema,
    FonteConfig,
    PosicaoNova,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp, ErroRede

URL = "https://dados.mobilidade.rio/gps/sppo"
JANELA = timedelta(minutes=3)  # sobrepõe a cadência de 1 min de propósito
FOLGA_FUTURO = timedelta(minutes=30)  # relógio da origem adiantado é normal; 3 h não é


class RegistroSppo(BaseModel):
    """Schema de um registro do payload do SPPO (formato GTFS, desde 2026-08-07)."""

    id_veiculo: str
    servico: str
    latitude: float
    longitude: float
    velocidade: float
    # `datetime` é nome reservado aqui; o alias mantém o contrato da origem
    datahora: datetime = Field(alias="datetime")
    sentido: str = ""
    direcao: float | None = None
    trip_id: str | None = None
    shape_id: str | None = None

    @field_validator("datahora", mode="before")
    @classmethod
    def _z_mentiroso_e_hora_do_rio(cls, bruto: object) -> object:
        """O sufixo Z é falso: o valor é hora local do Rio (ver docstring do módulo)."""
        if isinstance(bruto, str):
            ingenuo = datetime.fromisoformat(bruto.removesuffix("Z"))
            return ingenuo.replace(tzinfo=TZ_RIO).astimezone(UTC)
        return bruto


def coletar_janela(cliente: ClienteHttp, inicio: datetime, fim: datetime) -> ResultadoColeta:
    """Coleta um intervalo arbitrário — a origem serve janelas passadas.

    `inicio` e `fim` são hora local do Rio, como a API exige. Separado de
    `coletar` pra que o backfill (`semente.gps_sppo`) use o mesmo parser.
    """
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
    if isinstance(registros, dict) and registros.get("RetornoOK") is False:
        # Backend antigo devolvia HTTP 200 com dict de erro em timeout interno
        # (visto em 2026-08-06). Mantido depois da troca de schema: se a camada
        # nova ainda expuser esse erro, classificar como schema marcaria a fonte
        # "fora" por uma falha que é transitória
        raise ErroRede(f"servidor SPPO com erro interno: {registros.get('DescricaoErro')}")
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
                veiculo_id=registro.id_veiculo,
                ts=registro.datahora,
                lat=registro.latitude,
                lon=registro.longitude,
                linha=registro.servico,
                velocidade=round(registro.velocidade),
                extra={
                    "sentido": registro.sentido,
                    "direcao": registro.direcao,
                    "trip_id": registro.trip_id,
                    "shape_id": registro.shape_id,
                },
            )
        )

    # Se a origem corrigir o Z pra UTC de verdade, a reetiquetagem acima passa a
    # jogar tudo 3 h pro futuro — e frescor só enxerga dado velho, então a falha
    # seria silenciosa. Acusa como schema, que é o que ela é.
    if marca_frescor and marca_frescor - datetime.now(tz=UTC) > FOLGA_FUTURO:
        raise ErroSchema(f"dado no futuro ({marca_frescor.isoformat()}): o Z virou UTC de verdade?")

    return ResultadoColeta(posicoes=posicoes, marca_frescor=marca_frescor)


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    fim = datetime.now(tz=TZ_RIO)
    return coletar_janela(cliente, fim - JANELA, fim)


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
