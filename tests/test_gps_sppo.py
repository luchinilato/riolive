"""Parser do GPS SPPO sobre payload real capturado em 2026-08-06."""

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from riolive.fontes import gps_sppo
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp, ErroRede


def _coletar_fixture(conteudo: bytes) -> gps_sppo.ResultadoColeta:
    with respx.mock:
        rota = respx.get(url__startswith=gps_sppo.URL).mock(
            return_value=httpx.Response(200, content=conteudo)
        )
        with ClienteHttp() as cliente:
            resultado = gps_sppo.coletar(cliente)
        # params obrigatórios em hora local presentes na chamada
        params = rota.calls.last.request.url.params
        assert "dataInicial" in params and "dataFinal" in params
    return resultado


def test_payload_real_vira_posicoes(fixtures: Path) -> None:
    conteudo = (fixtures / "gps_sppo.json").read_bytes()
    resultado = _coletar_fixture(conteudo)
    assert len(resultado.posicoes) == 200
    assert {p.modal for p in resultado.posicoes} == {"onibus"}


def test_virgula_decimal_e_epoch_ms_convertidos(fixtures: Path) -> None:
    registros = json.loads((fixtures / "gps_sppo.json").read_text())
    primeiro = registros[0]  # C27173: "-22,81702" / datahora "1785992448000"
    resultado = _coletar_fixture(json.dumps([primeiro]).encode())
    posicao = resultado.posicoes[0]
    assert posicao.veiculo_id == "C27173"
    assert posicao.lat == pytest.approx(-22.81702)
    assert posicao.lon == pytest.approx(-43.30144)
    assert posicao.ts == datetime.fromtimestamp(1785992448, tz=UTC)
    assert posicao.velocidade == 0
    assert posicao.linha == "SN639"


def test_coordenada_implausivel_e_descartada() -> None:
    glitch = {
        "ordem": "X00000",
        "latitude": "0,0",
        "longitude": "0,0",
        "datahora": "1785992448000",
        "velocidade": "10",
        "linha": "100",
    }
    resultado = _coletar_fixture(json.dumps([glitch]).encode())
    assert resultado.posicoes == []


def test_marca_frescor_e_o_ts_mais_novo(fixtures: Path) -> None:
    conteudo = (fixtures / "gps_sppo.json").read_bytes()
    resultado = _coletar_fixture(conteudo)
    assert resultado.marca_frescor == max(p.ts for p in resultado.posicoes)


def test_payload_nao_lista_e_falha_de_schema() -> None:
    with respx.mock:
        respx.get(url__startswith=gps_sppo.URL).mock(
            return_value=httpx.Response(200, json={"erro": "manutencao"})
        )
        with ClienteHttp() as cliente, pytest.raises(ErroSchema):
            gps_sppo.coletar(cliente)


def test_timeout_interno_do_backend_e_falha_de_rede() -> None:
    # Payload real de 2026-08-06: HTTP 200 com dict de erro — transitório, não schema
    erro = {
        "RetornoOK": False,
        "IdentificacaoLogin": None,
        "DescricaoErro": "Execution Timeout Expired.",
        "Empresas": None,
    }
    with respx.mock:
        respx.get(url__startswith=gps_sppo.URL).mock(return_value=httpx.Response(200, json=erro))
        with ClienteHttp() as cliente, pytest.raises(ErroRede):
            gps_sppo.coletar(cliente)
