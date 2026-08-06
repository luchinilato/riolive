"""Parser do Alerta Rio sobre o Chuvas.xml real capturado em 2026-08-06."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from riolive.fontes import alerta_rio
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp
from riolive.modelos import METRICAS


def _coletar_fixture(fixtures: Path) -> alerta_rio.ResultadoColeta:
    conteudo = (fixtures / "alerta_rio_chuvas.xml").read_bytes()
    with respx.mock:
        respx.get(alerta_rio.URL_XML).mock(return_value=httpx.Response(200, content=conteudo))
        with ClienteHttp() as cliente:
            return alerta_rio.coletar(cliente)


def test_todas_as_estacoes_viram_locais(fixtures: Path) -> None:
    resultado = _coletar_fixture(fixtures)
    # 33 estações; as 8 meteorológicas são subconjunto que também mede chuva
    assert len(resultado.locais) == 33
    assert sum(1 for local in resultado.locais if local.tipo == "meteorologica") == 8
    vidigal = next(local for local in resultado.locais if local.nome == "Vidigal")
    assert vidigal.lat == pytest.approx(-22.9925)
    assert vidigal.lon == pytest.approx(-43.233056)
    assert vidigal.extra == {"bacia": "Zona Sul"}


def test_metricas_no_vocabulario_controlado(fixtures: Path) -> None:
    resultado = _coletar_fixture(fixtures)
    assert resultado.medicoes
    metricas_usadas = {medicao.metrica for medicao in resultado.medicoes}
    assert metricas_usadas <= METRICAS


def test_timestamp_local_convertido_pra_utc(fixtures: Path) -> None:
    resultado = _coletar_fixture(fixtures)
    # Leitura das 01:55 hora do Rio (UTC-3) = 04:55 UTC
    chuva_vidigal = next(
        m for m in resultado.medicoes if m.codigo_local == "1" and m.metrica == "chuva_15min"
    )
    assert chuva_vidigal.ts == datetime(2026, 8, 6, 4, 55, tzinfo=UTC)
    assert resultado.marca_frescor is not None
    assert resultado.marca_frescor.tzinfo is not None


def test_valores_none_sao_pulados(fixtures: Path) -> None:
    # Vidigal (met) reporta pressao="None": não pode virar medição
    resultado = _coletar_fixture(fixtures)
    metricas_vidigal = {m.metrica for m in resultado.medicoes if m.codigo_local == "1"}
    assert "pressao_hpa" not in metricas_vidigal
    assert "vento_kmh" in metricas_vidigal


def test_xml_sem_estacoes_e_falha_de_schema() -> None:
    with respx.mock:
        respx.get(alerta_rio.URL_XML).mock(return_value=httpx.Response(200, content=b"<estacoes/>"))
        with ClienteHttp() as cliente, pytest.raises(ErroSchema):
            alerta_rio.coletar(cliente)


def test_html_no_lugar_do_xml_e_falha_de_schema() -> None:
    with respx.mock:
        respx.get(alerta_rio.URL_XML).mock(
            return_value=httpx.Response(200, content=b"<html><body>manutencao</body></html>")
        )
        with ClienteHttp() as cliente, pytest.raises(ErroSchema):
            alerta_rio.coletar(cliente)
