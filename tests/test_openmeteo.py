"""Parser do Open-Meteo sobre resposta real (2 pontos) capturada em 2026-08-06."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from riolive.fontes import openmeteo
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp

PONTOS_TESTE = {
    "centro": ("Centro", -22.905, -43.195),
    "zona_sul": ("Zona Sul", -22.97, -43.19),
}


def _coletar(conteudo: bytes) -> openmeteo.ResultadoColeta:
    coletar = openmeteo._coletar(
        openmeteo.URL_TEMPO, PONTOS_TESTE, openmeteo.VARIAVEIS_TEMPO, "ponto_previsao"
    )
    with respx.mock:
        respx.get(url__startswith=openmeteo.URL_TEMPO).mock(
            return_value=httpx.Response(200, content=conteudo)
        )
        with ClienteHttp() as cliente:
            return coletar(cliente)


def test_multiponto_vira_previsoes_por_codigo(fixtures: Path) -> None:
    resultado = _coletar((fixtures / "openmeteo_tempo.json").read_bytes())
    codigos = {p.codigo_local for p in resultado.previsoes}
    assert codigos == {"centro", "zona_sul"}
    metricas = {p.metrica for p in resultado.previsoes}
    assert "temp_c" in metricas and "precipitacao_mm" in metricas
    assert len(resultado.locais) == 2
    # sem marca de frescor: previsão não congela
    assert resultado.marca_frescor is None


def test_iso_ingenuo_vira_utc_aware(fixtures: Path) -> None:
    resultado = _coletar((fixtures / "openmeteo_tempo.json").read_bytes())
    primeira = min(p.ts_alvo for p in resultado.previsoes)
    assert primeira == datetime(2026, 8, 6, 0, 0, tzinfo=UTC)
    assert all(p.ts_alvo.tzinfo is not None for p in resultado.previsoes)


def test_resposta_sem_hourly_e_falha_de_schema() -> None:
    with pytest.raises(ErroSchema):
        _coletar(b'[{"erro": 1}, {"erro": 2}]')


def test_numero_de_pontos_divergente_e_falha_de_schema(fixtures: Path) -> None:
    import json

    um_so = json.loads((fixtures / "openmeteo_tempo.json").read_text())[:1]
    with pytest.raises(ErroSchema):
        _coletar(json.dumps(um_so).encode())
