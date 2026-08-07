"""Alerta Rio: 33 estações pluviométricas da Prefeitura, das quais 8 (type="met")
também são meteorológicas.

Fonte primária: `upload/xml/Chuvas.xml` — XML estruturado com id, nome, tipo,
lat/lon e bacia de cada estação, janelas de chuva (5min..mês) e leituras met,
com timestamp próprio por estação. Achado em 2026-08-06; o catálogo previa raspar
o HTML de TempoReal.html (que segue como fallback documentado, mesmo servidor).

Pegadinhas: timestamps ingênuos em hora do Rio; valor "None" em atributos met;
atributo pode faltar. Cadência real do dado: ~5 min.
"""

from datetime import datetime, timedelta

from defusedxml import ElementTree
from pydantic import BaseModel

from riolive.fontes.comum import local_para_utc
from riolive.ingestao.contrato import (
    ErroSchema,
    FonteConfig,
    LocalNovo,
    MedicaoNova,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp

URL_XML = "https://sistema-alerta-rio.com.br/upload/xml/Chuvas.xml"

METRICAS_CHUVA = {
    "m05": "chuva_5min",
    "m10": "chuva_10min",
    "m15": "chuva_15min",
    "h01": "chuva_1h",
    "h04": "chuva_4h",
    "h24": "chuva_24h",
    "h96": "chuva_96h",
    "mes": "chuva_mes",
}
METRICAS_MET = {
    "temperatura": "temp_c",
    "sensacao": "sensacao_termica_c",
    "umidade": "umidade_pct",
    "pressao": "pressao_hpa",
    "velvento": "vento_kmh",
    "dirvento": "vento_direcao_graus",
}
TIPOS_ESTACAO = {"plv": "pluviometro", "met": "meteorologica"}


class EstacaoXml(BaseModel):
    """Schema de uma <estacao> do Chuvas.xml (validação Pydantic da fonte)."""

    id: str
    nome: str
    tipo: str
    lat: float
    lon: float
    bacia: str | None
    hora_chuvas: datetime | None
    chuvas: dict[str, float]
    met: dict[str, float]


def _valor(atributos: dict[str, str], chave: str) -> float | None:
    bruto = atributos.get(chave)
    if bruto is None or bruto in ("None", "-", ""):
        return None
    return float(bruto)


def _interpretar_estacao(elemento: object) -> EstacaoXml:
    atrib = elemento.attrib  # type: ignore[attr-defined]
    localizacao = elemento.find("localizacao")  # type: ignore[attr-defined]
    chuvas = elemento.find("chuvas")  # type: ignore[attr-defined]
    met = elemento.find("met")  # type: ignore[attr-defined]
    if localizacao is None:
        raise ErroSchema(f"estação {atrib.get('id')} sem <localizacao>")

    valores_chuva: dict[str, float] = {}
    hora_chuvas: datetime | None = None
    if chuvas is not None:
        hora_bruta = chuvas.attrib.get("hora")
        if hora_bruta:
            hora_chuvas = datetime.fromisoformat(hora_bruta)
        for chave, metrica in METRICAS_CHUVA.items():
            valor = _valor(chuvas.attrib, chave)
            if valor is not None:
                valores_chuva[metrica] = valor

    valores_met: dict[str, float] = {}
    if met is not None:
        for chave, metrica in METRICAS_MET.items():
            valor = _valor(met.attrib, chave)
            if valor is not None:
                valores_met[metrica] = valor

    return EstacaoXml(
        id=atrib["id"],
        nome=atrib["nome"],
        tipo=TIPOS_ESTACAO.get(atrib.get("type", ""), "pluviometro"),
        lat=float(localizacao.attrib["latitude"]),
        lon=float(localizacao.attrib["longitude"]),
        bacia=localizacao.attrib.get("bacia"),
        hora_chuvas=hora_chuvas,
        chuvas=valores_chuva,
        met=valores_met,
    )


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    resposta = cliente.obter(URL_XML)
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} no Chuvas.xml")
    try:
        raiz = ElementTree.fromstring(resposta.content)
    except ElementTree.ParseError as exc:
        raise ErroSchema(f"XML inválido: {exc}") from exc
    elementos = raiz.findall("estacao")
    if not elementos:
        raise ErroSchema("XML sem elementos <estacao>")

    locais: list[LocalNovo] = []
    medicoes: list[MedicaoNova] = []
    marca_frescor: datetime | None = None

    for elemento in elementos:
        estacao = _interpretar_estacao(elemento)
        locais.append(
            LocalNovo(
                codigo_externo=estacao.id,
                nome=estacao.nome,
                tipo=estacao.tipo,
                lat=estacao.lat,
                lon=estacao.lon,
                extra={"bacia": estacao.bacia} if estacao.bacia else None,
            )
        )
        if estacao.hora_chuvas is None:
            continue
        ts = local_para_utc(estacao.hora_chuvas)
        marca_frescor = max(marca_frescor, ts) if marca_frescor else ts
        for metrica, valor in {**estacao.chuvas, **estacao.met}.items():
            medicoes.append(
                MedicaoNova(codigo_local=estacao.id, metrica=metrica, ts=ts, valor=valor)
            )

    return ResultadoColeta(medicoes=medicoes, locais=locais, marca_frescor=marca_frescor)


FONTE = FonteConfig(
    slug="alerta_rio",
    nome="Alerta Rio — pluviômetros e meteorologia",
    orgao="Prefeitura do Rio / Alerta Rio",
    url=URL_XML,
    bloco="A",
    criticidade=5,
    cadencia=timedelta(minutes=5),
    tolerancia_frescor=timedelta(minutes=30),
    coletar=coletar,
)
