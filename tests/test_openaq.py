"""Parser do OpenAQ sobre payloads reais capturados em 2026-08-06."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from riolive.fontes import openaq
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp


@pytest.fixture(autouse=True)
def _chave_de_teste(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RIOLIVE_OPENAQ_API_KEY", "chave-de-teste")
    from riolive.config import config

    config.cache_clear()


def _coletar_fixture(fixtures: Path) -> openaq.ResultadoColeta:
    locations = (fixtures / "openaq_locations.json").read_bytes()
    latest = (fixtures / "openaq_latest.json").read_bytes()
    with respx.mock:
        rota_loc = respx.get(f"{openaq.URL_BASE}/locations").mock(
            return_value=httpx.Response(200, content=locations)
        )
        # a estação 820323 responde com a fixture real; as demais, vazio
        respx.get(f"{openaq.URL_BASE}/locations/820323/latest").mock(
            return_value=httpx.Response(200, content=latest)
        )
        respx.get(url__regex=rf"{openaq.URL_BASE}/locations/\d+/latest").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        with ClienteHttp() as cliente:
            resultado = openaq.coletar(cliente)
        assert rota_loc.calls.last.request.headers["X-API-Key"] == "chave-de-teste"
    return resultado


def test_estacoes_com_sensores_uteis_viram_locais(fixtures: Path) -> None:
    resultado = _coletar_fixture(fixtures)
    assert len(resultado.locais) >= 25  # 28 no raio; só cai quem não tem sensor mapeável
    centro = next(local for local in resultado.locais if local.codigo_externo == "820323")
    assert centro.tipo == "estacao_ar"
    assert centro.lat == pytest.approx(-22.9084)


def test_leitura_mapeia_sensor_pra_metrica(fixtures: Path) -> None:
    resultado = _coletar_fixture(fixtures)
    # fixture latest: sensor 14798912 (pm25) da estação 820323, 8.21 µg/m³ às 12:00Z
    pm25 = next(m for m in resultado.medicoes if m.codigo_local == "820323" and m.metrica == "pm25")
    assert pm25.valor == pytest.approx(8.21)
    assert pm25.ts == datetime(2026, 8, 6, 12, 0, tzinfo=UTC)
    assert pm25.payload == {"unidades": "µg/m³"}
    assert resultado.marca_frescor is not None


def test_sem_estacoes_e_falha_de_schema() -> None:
    with respx.mock:
        respx.get(f"{openaq.URL_BASE}/locations").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        with ClienteHttp() as cliente, pytest.raises(ErroSchema):
            openaq.coletar(cliente)


def test_chave_ausente_e_defeito_nosso(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RIOLIVE_OPENAQ_API_KEY", "")
    from riolive.config import config

    config.cache_clear()
    with ClienteHttp() as cliente, pytest.raises(RuntimeError, match="OPENAQ"):
        openaq.coletar(cliente)
