"""Fetcher genérico: retry em 5xx/transporte, 4xx passa pro parser, user-agent identificado."""

import httpx
import pytest
import respx

from riolive.ingestao.fetcher import ClienteHttp, ErroRede

URL = "https://exemplo.rio/dados"


@respx.mock
def test_retry_em_5xx_ate_suceder() -> None:
    rota = respx.get(URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(503), httpx.Response(200, text="ok")]
    )
    with ClienteHttp() as cliente:
        resposta = cliente.obter(URL)
    assert resposta.status_code == 200
    assert rota.call_count == 3


@respx.mock
def test_5xx_persistente_vira_erro_rede() -> None:
    respx.get(URL).mock(return_value=httpx.Response(500))
    with ClienteHttp() as cliente, pytest.raises(ErroRede):
        cliente.obter(URL)


@respx.mock
def test_timeout_vira_erro_rede() -> None:
    respx.get(URL).mock(side_effect=httpx.ConnectTimeout("timeout"))
    with ClienteHttp() as cliente, pytest.raises(ErroRede):
        cliente.obter(URL)


@respx.mock
def test_4xx_nao_e_erro_de_rede() -> None:
    # Contrato quebrado (404, 401...) é classe schema: decisão do parser, não do fetcher
    respx.get(URL).mock(return_value=httpx.Response(404))
    with ClienteHttp() as cliente:
        assert cliente.obter(URL).status_code == 404


@respx.mock
def test_user_agent_identificado() -> None:
    rota = respx.get(URL).mock(return_value=httpx.Response(200))
    with ClienteHttp() as cliente:
        cliente.obter(URL)
    assert "riolive" in rota.calls.last.request.headers["User-Agent"]
