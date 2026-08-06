"""Previsão do tempo e do mar via Open-Meteo (sem auth, testada no catálogo).

Duas fontes num módulo: `previsao_tempo` (5 pontos, um por zona da cidade) e
`previsao_mar` (2 pontos no litoral). Cada rodada de coleta insere a previsão
horária de 48 h com `emitida_em` = instante da coleta — todas as rodadas são
preservadas (decisão A de 2026-08-06), o painel lê vw_previsao_atual.

Sem marca de frescor: previsão aponta pro futuro, o detector de congelamento
não se aplica (falha aqui é rede ou schema).
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from riolive.ingestao.contrato import (
    ErroSchema,
    FonteConfig,
    LocalNovo,
    PrevisaoNova,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp

URL_TEMPO = "https://api.open-meteo.com/v1/forecast"
URL_MAR = "https://marine-api.open-meteo.com/v1/marine"

PONTOS_TEMPO = {
    "centro": ("Centro", -22.905, -43.195),
    "zona_sul": ("Zona Sul (Copacabana)", -22.97, -43.19),
    "zona_norte": ("Zona Norte (Irajá)", -22.84, -43.33),
    "zona_oeste": ("Zona Oeste (Campo Grande)", -22.90, -43.56),
    "barra": ("Barra da Tijuca", -23.00, -43.37),
}
PONTOS_MAR = {
    "mar_copacabana": ("Mar de Copacabana", -22.995, -43.17),
    "mar_barra": ("Mar da Barra", -23.03, -43.35),
}

VARIAVEIS_TEMPO = {
    "temperature_2m": "temp_c",
    "precipitation": "precipitacao_mm",
    "precipitation_probability": "prob_precipitacao_pct",
    "wind_speed_10m": "vento_kmh",
    "relative_humidity_2m": "umidade_pct",
}
VARIAVEIS_MAR = {
    "wave_height": "onda_altura_m",
    "wave_period": "onda_periodo_s",
    "wave_direction": "onda_direcao_graus",
}


def _interpretar_ponto(
    corpo: dict[str, Any], codigo: str, variaveis: dict[str, str]
) -> list[PrevisaoNova]:
    horaria = corpo.get("hourly")
    if not isinstance(horaria, dict) or "time" not in horaria:
        raise ErroSchema(f"resposta sem bloco hourly pro ponto {codigo}")
    # timezone=UTC no request; o ISO vem ingênuo ("2026-08-06T14:00")
    instantes = [datetime.fromisoformat(bruto).replace(tzinfo=UTC) for bruto in horaria["time"]]
    previsoes: list[PrevisaoNova] = []
    for variavel, metrica in variaveis.items():
        valores = horaria.get(variavel)
        if valores is None:
            continue
        for ts_alvo, valor in zip(instantes, valores, strict=True):
            if valor is None:
                continue
            previsoes.append(
                PrevisaoNova(codigo_local=codigo, metrica=metrica, ts_alvo=ts_alvo, valor=valor)
            )
    return previsoes


def _coletar(
    url: str,
    pontos: dict[str, tuple[str, float, float]],
    variaveis: dict[str, str],
    tipo_local: str,
) -> Any:
    def coletar(cliente: ClienteHttp) -> ResultadoColeta:
        codigos = list(pontos)
        resposta = cliente.obter(
            url,
            params={
                "latitude": ",".join(str(pontos[c][1]) for c in codigos),
                "longitude": ",".join(str(pontos[c][2]) for c in codigos),
                "hourly": ",".join(variaveis),
                "forecast_days": "2",
                "timezone": "UTC",
            },
        )
        if resposta.status_code != 200:
            raise ErroSchema(f"HTTP {resposta.status_code} no Open-Meteo")
        corpo = resposta.json()
        # 1 ponto → objeto; N pontos → lista na mesma ordem do request
        respostas = corpo if isinstance(corpo, list) else [corpo]
        if len(respostas) != len(codigos):
            raise ErroSchema(f"esperava {len(codigos)} pontos, vieram {len(respostas)}")

        previsoes: list[PrevisaoNova] = []
        for codigo, item in zip(codigos, respostas, strict=True):
            previsoes.extend(_interpretar_ponto(item, codigo, variaveis))
        if not previsoes:
            raise ErroSchema("Open-Meteo sem nenhum valor de previsão")

        locais = [
            LocalNovo(
                codigo_externo=c,
                nome=pontos[c][0],
                tipo=tipo_local,
                lat=pontos[c][1],
                lon=pontos[c][2],
            )
            for c in codigos
        ]
        return ResultadoColeta(previsoes=previsoes, locais=locais)

    return coletar


FONTE_TEMPO = FonteConfig(
    slug="previsao_tempo",
    nome="Previsão do tempo (Open-Meteo)",
    orgao="Open-Meteo",
    url=URL_TEMPO,
    bloco="A",
    criticidade=2,
    cadencia=timedelta(hours=3),
    tolerancia_frescor=timedelta(days=365),  # previsão não congela; falha é rede/schema
    coletar=_coletar(URL_TEMPO, PONTOS_TEMPO, VARIAVEIS_TEMPO, "ponto_previsao"),
    licenca="CC-BY 4.0",
)

FONTE_MAR = FonteConfig(
    slug="previsao_mar",
    nome="Previsão do mar (Open-Meteo Marine)",
    orgao="Open-Meteo",
    url=URL_MAR,
    bloco="A",
    criticidade=2,
    cadencia=timedelta(hours=3),
    tolerancia_frescor=timedelta(days=365),
    coletar=_coletar(URL_MAR, PONTOS_MAR, VARIAVEIS_MAR, "ponto_previsao_mar"),
    licenca="CC-BY 4.0",
)
