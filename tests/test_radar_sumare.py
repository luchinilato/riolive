"""Fonte do radar: quadros PNG viram blobs com timestamp do Last-Modified."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from riolive.fontes import radar_sumare
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp

PNG_MINIMO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def test_quadros_viram_blobs_com_ts_do_last_modified() -> None:
    with respx.mock:
        respx.get(url__startswith=radar_sumare.URL_BASE).mock(
            return_value=httpx.Response(
                200,
                content=PNG_MINIMO,
                headers={"Last-Modified": "Thu, 06 Aug 2026 13:31:05 GMT"},
            )
        )
        with ClienteHttp() as cliente:
            resultado = radar_sumare.coletar(cliente)
    assert len(resultado.blobs) == 20
    blob = resultado.blobs[0]
    assert blob.ts == datetime(2026, 8, 6, 13, 31, 5, tzinfo=UTC)
    assert blob.caminho == "radar/2026/08/20260806_133105.png"
    assert blob.meta is not None and blob.meta["bounds"] == radar_sumare.BOUNDS
    assert resultado.marca_frescor == blob.ts


def test_html_no_lugar_do_png_e_falha_de_schema() -> None:
    with respx.mock:
        respx.get(url__startswith=radar_sumare.URL_BASE).mock(
            return_value=httpx.Response(
                200,
                content=b"<html>manutencao</html>",
                headers={"Last-Modified": "Thu, 06 Aug 2026 13:31:05 GMT"},
            )
        )
        with ClienteHttp() as cliente, pytest.raises(ErroSchema):
            radar_sumare.coletar(cliente)


def test_todos_os_quadros_indisponiveis_e_falha() -> None:
    with respx.mock:
        respx.get(url__startswith=radar_sumare.URL_BASE).mock(return_value=httpx.Response(404))
        with ClienteHttp() as cliente, pytest.raises(ErroSchema):
            radar_sumare.coletar(cliente)
