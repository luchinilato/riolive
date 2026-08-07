"""Velocidade nos corredores prioritários via TomTom Flow Segment (com chave).

Estratégia da DEC: a camada base de trânsito é a velocidade derivada da NOSSA
frota; o TomTom entra amostrado nos corredores, dentro do free tier (20k
req/mês). Política de amostragem: no pico (6–10 e 16–20, hora do Rio) coleta a
cada rodada de 15 min; fora do pico, só na hora cheia. 12 corredores ≈ 17,3k
req/mês.

Lista de corredores proposta em 2026-08-06 (Luciano pode editar à vontade —
o ponto é "snapado" pro segmento mais próximo pela API).
"""

from datetime import UTC, datetime, timedelta

from riolive.config import config
from riolive.fontes.comum import TZ_RIO
from riolive.ingestao.contrato import (
    ErroSchema,
    FonteConfig,
    LocalNovo,
    MedicaoNova,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp

URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

# codigo → (nome, lat, lon)
CORREDORES = {
    "av_brasil_caju": ("Av. Brasil · Caju", -22.8830, -43.2260),
    "av_brasil_penha": ("Av. Brasil · Penha", -22.8410, -43.2810),
    "av_brasil_bangu": ("Av. Brasil · Bangu", -22.8620, -43.4680),
    "linha_amarela": ("Linha Amarela · Del Castilho", -22.8770, -43.2740),
    "linha_vermelha": ("Linha Vermelha · Maré", -22.8560, -43.2430),
    "aterro": ("Aterro do Flamengo", -22.9350, -43.1710),
    "reboucas": ("Túnel Rebouças", -22.9440, -43.1970),
    "av_americas": ("Av. das Américas · Barra", -23.0000, -43.3650),
    "ayrton_senna": ("Av. Ayrton Senna", -22.9730, -43.3650),
    "ponte": ("Ponte Rio–Niterói · acesso", -22.8710, -43.2130),
    "pres_vargas": ("Av. Presidente Vargas", -22.9050, -43.1900),
    "grajau_jpa": ("Grajaú–Jacarepaguá", -22.9420, -43.2820),
}
HORAS_PICO = set(range(6, 10)) | set(range(16, 20))


def _dentro_da_janela(agora: datetime) -> bool:
    if agora.hour in HORAS_PICO:
        return True
    return agora.minute < 15  # fora do pico: só a rodada da hora cheia


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    chave = config().tomtom_api_key.get_secret_value()
    if not chave:
        raise RuntimeError("RIOLIVE_TOMTOM_API_KEY não configurada no .env")

    agora_rio = datetime.now(tz=TZ_RIO)
    if not _dentro_da_janela(agora_rio):
        return ResultadoColeta()  # fora da política de amostragem: rodada vazia é sucesso

    locais = [
        LocalNovo(codigo_externo=codigo, nome=nome, tipo="corredor", lat=lat, lon=lon)
        for codigo, (nome, lat, lon) in CORREDORES.items()
    ]
    medicoes: list[MedicaoNova] = []
    marca_frescor = None
    falhas = 0
    for codigo, (_nome, lat, lon) in CORREDORES.items():
        resposta = cliente.obter(URL, params={"point": f"{lat},{lon}", "key": chave})
        if resposta.status_code != 200:
            falhas += 1
            continue
        dados = resposta.json().get("flowSegmentData")
        if not dados:
            falhas += 1
            continue
        ts = datetime.now(tz=UTC)
        marca_frescor = max(marca_frescor, ts) if marca_frescor else ts
        for metrica, campo in (("vel_kmh", "currentSpeed"), ("vel_livre_kmh", "freeFlowSpeed")):
            valor = dados.get(campo)
            if valor is not None:
                medicoes.append(
                    MedicaoNova(
                        codigo_local=codigo,
                        metrica=metrica,
                        ts=ts,
                        valor=float(valor),
                        payload={"confianca": dados.get("confidence")},
                    )
                )
    if falhas == len(CORREDORES):
        raise ErroSchema("nenhum corredor respondeu no TomTom")
    return ResultadoColeta(medicoes=medicoes, locais=locais, marca_frescor=marca_frescor)


FONTE = FonteConfig(
    slug="transito_tomtom",
    nome="Velocidade nos corredores (TomTom)",
    orgao="TomTom Traffic",
    url=URL,
    bloco="B",
    criticidade=3,
    cadencia=timedelta(minutes=15),
    tolerancia_frescor=timedelta(hours=2),
    coletar=coletar,
)
