"""Parser do GPS SPPO sobre payload real capturado em 2026-08-07 (schema GTFS novo)."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
import respx
from pydantic import ValidationError

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


def _registro(**sobrescreve: object) -> dict[str, object]:
    """Registro no formato da origem (2026-08-07), pra montar casos de borda."""
    base: dict[str, object] = {
        "id_veiculo": "B71099",
        "servico": "456",
        "sentido": "I",
        "latitude": -22.9677219,
        "longitude": -43.18443,
        "velocidade": 35.0,
        "direcao": 232.05,
        "route_id": None,
        "trip_id": "4ce921fc-753a-4aac-b43a-06b9be2d938b",
        "shape_id": "O0456AAA0AIDU01",
        "datetime": "2026-08-07T02:03:48Z",
        "datetime_envio": "2026-08-07T02:03:59Z",
        "datetime_servidor": "2026-08-07T02:04:26Z",
    }
    return base | sobrescreve


def test_campos_do_schema_gtfs_viram_posicao(fixtures: Path) -> None:
    registros = json.loads((fixtures / "gps_sppo.json").read_text())
    resultado = _coletar_fixture(json.dumps([registros[0]]).encode())
    posicao = resultado.posicoes[0]
    assert posicao.veiculo_id == "B71099"  # era `ordem` no schema antigo
    assert posicao.linha == "456"  # era `linha`, agora `servico`
    assert posicao.lat == pytest.approx(-22.9677219)
    assert posicao.lon == pytest.approx(-43.18443)
    # "2026-08-07T02:03:48Z" é hora do Rio apesar do Z: vira 05:03:48 UTC
    assert posicao.ts == datetime(2026, 8, 7, 5, 3, 48, tzinfo=UTC)
    assert posicao.velocidade == 35


def test_z_da_origem_e_hora_do_rio_nao_utc() -> None:
    # Sem a reetiquetagem, todo ponto entraria 3 h no passado e a série sairia
    # torta em silêncio. Foi o que a máquina de saúde pegou em 2026-08-07.
    resultado = _coletar_fixture(json.dumps([_registro(datetime="2026-08-06T12:00:00Z")]).encode())
    assert resultado.posicoes[0].ts == datetime(2026, 8, 6, 15, 0, 0, tzinfo=UTC)


def test_dado_no_futuro_acusa_schema() -> None:
    # Se a origem consertar o Z, a reetiquetagem vira erro de 3 h pro futuro —
    # frescor não pega dado adiantado, então a fonte tem que gritar aqui
    futuro = datetime.now(tz=UTC) + timedelta(hours=3)
    registro = _registro(datetime=futuro.strftime("%Y-%m-%dT%H:%M:%SZ"))
    with pytest.raises(ErroSchema, match="futuro"):
        _coletar_fixture(json.dumps([registro]).encode())


def test_viagem_do_gtfs_vai_pro_extra() -> None:
    resultado = _coletar_fixture(json.dumps([_registro()]).encode())
    assert resultado.posicoes[0].extra == {
        "sentido": "I",
        "direcao": 232.05,
        "trip_id": "4ce921fc-753a-4aac-b43a-06b9be2d938b",
        "shape_id": "O0456AAA0AIDU01",
    }


def test_sentido_vazio_e_aceito() -> None:
    # ~30% dos registros vêm com sentido "" — não é motivo pra recusar o ponto
    resultado = _coletar_fixture(json.dumps([_registro(sentido="")]).encode())
    assert resultado.posicoes[0].extra is not None
    assert resultado.posicoes[0].extra["sentido"] == ""


def test_schema_antigo_e_falha_de_schema() -> None:
    # Se a origem voltar ao formato pré-2026-08-07, a fonte tem que acusar,
    # não gravar meio dado: foi assim que a troca apareceu em produção
    antigo = {
        "ordem": "C27173",
        "latitude": "-22,81702",
        "longitude": "-43,30144",
        "datahora": "1785992448000",
        "velocidade": "0",
        "linha": "SN639",
    }
    with pytest.raises(ValidationError):
        _coletar_fixture(json.dumps([antigo]).encode())


def test_coordenada_implausivel_e_descartada() -> None:
    glitch = _registro(id_veiculo="X00000", latitude=0.0, longitude=0.0)
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
