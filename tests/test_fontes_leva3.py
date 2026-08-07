"""Leva de fontes de 2026-08-06: adsb.lol, MetrôRio, jogos, Águas do Rio, TomTom."""

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from riolive.fontes import aguas_rio, ceu_adsb, jogos, metro_rio, transito_tomtom
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp

# ---------------- adsb.lol ----------------


def test_adsb_payload_real_vira_posicoes(fixtures: Path) -> None:
    with respx.mock:
        respx.get(url__startswith=ceu_adsb.URL).mock(
            return_value=httpx.Response(200, content=(fixtures / "adsb.json").read_bytes())
        )
        with ClienteHttp() as cliente:
            resultado = ceu_adsb.coletar(cliente)
    assert resultado.posicoes
    aviao = resultado.posicoes[0]
    assert aviao.modal == "aviao"
    assert len(aviao.veiculo_id) == 6  # hex ICAO
    assert resultado.marca_frescor is not None


def test_adsb_ceu_vazio_e_sucesso() -> None:
    with respx.mock:
        respx.get(url__startswith=ceu_adsb.URL).mock(
            return_value=httpx.Response(200, json={"ac": [], "total": 0})
        )
        with ClienteHttp() as cliente:
            resultado = ceu_adsb.coletar(cliente)
    assert resultado.posicoes == []
    assert resultado.marca_frescor is not None  # frescor cobre a fonte, não o movimento


# ---------------- MetrôRio ----------------

SCRIPT_METRO = b"const options = { token: 'tok-teste-123' };"


def _coletar_metro(status_json: bytes) -> metro_rio.ResultadoColeta:
    with respx.mock:
        respx.get(metro_rio.URL_SCRIPT).mock(return_value=httpx.Response(200, content=SCRIPT_METRO))
        rota = respx.get(metro_rio.URL_STATUS).mock(
            return_value=httpx.Response(200, content=status_json)
        )
        with ClienteHttp() as cliente:
            resultado = metro_rio.coletar(cliente)
        assert rota.calls.last.request.headers["Authorization"] == "Bearer tok-teste-123"
    return resultado


def test_metro_normal_gera_encerramentos(fixtures: Path) -> None:
    resultado = _coletar_metro((fixtures / "metro_status.json").read_bytes())
    assert len(resultado.eventos) == 3  # L1, L2, L4
    assert all(e.encerrar for e in resultado.eventos)  # tudo Normal na fixture


def test_metro_anormal_vira_evento_vigente() -> None:
    corpo = json.dumps(
        [
            {"linha": 1, "status": "Normal"},
            {"linha": 2, "status": "Operação parcial"},
        ]
    ).encode()
    resultado = _coletar_metro(corpo)
    anormal = next(e for e in resultado.eventos if e.tipo == "metro_l2")
    assert anormal.vigente and anormal.severidade == 3
    assert "parcial" in anormal.titulo.lower()
    normal = next(e for e in resultado.eventos if e.tipo == "metro_l1")
    assert normal.encerrar


def test_metro_token_ausente_e_falha_de_schema() -> None:
    with respx.mock:
        respx.get(metro_rio.URL_SCRIPT).mock(return_value=httpx.Response(200, content=b"vazio"))
        with ClienteHttp() as cliente, pytest.raises(ErroSchema):
            metro_rio.coletar(cliente)


# ---------------- jogos ----------------


def test_jogo_no_maracana_vira_evento_com_pino(fixtures: Path) -> None:
    conteudo = (fixtures / "tsdb_fla.json").read_bytes()
    with respx.mock:
        respx.get(url__startswith=jogos.URL_BASE).mock(
            return_value=httpx.Response(200, content=conteudo)
        )
        with ClienteHttp() as cliente:
            resultado = jogos.coletar(cliente)
    maraca = [e for e in resultado.eventos if "Maracan" in (e.payload or {}).get("estadio", "")]
    assert maraca
    jogo = maraca[0]
    assert jogo.tipo == "jogo"
    assert jogo.lat == pytest.approx(-22.9121)
    assert jogo.fim is not None and jogo.fim > jogo.inicio


def test_jogo_fora_da_cidade_e_filtrado() -> None:
    corpo = json.dumps(
        {
            "events": [
                {
                    "strEvent": "Bahia vs Flamengo",
                    "strVenue": "Arena Fonte Nova",
                    "strTimestamp": "2026-08-16T20:00:00",
                }
            ]
        }
    ).encode()
    with respx.mock:
        respx.get(url__startswith=jogos.URL_BASE).mock(
            return_value=httpx.Response(200, content=corpo)
        )
        with ClienteHttp() as cliente:
            resultado = jogos.coletar(cliente)
    assert resultado.eventos == []


# ---------------- Águas do Rio ----------------


def test_aguas_posts_viram_eventos_pontuais(fixtures: Path) -> None:
    with respx.mock:
        respx.get(url__startswith=aguas_rio.URL).mock(
            return_value=httpx.Response(200, content=(fixtures / "aguas.json").read_bytes())
        )
        with ClienteHttp() as cliente:
            resultado = aguas_rio.coletar(cliente)
    assert len(resultado.eventos) == 5
    evento = resultado.eventos[0]
    assert evento.tipo == "agua"
    assert evento.titulo.startswith("Águas do Rio:")
    assert "<" not in evento.titulo  # HTML limpo
    assert evento.fim == evento.inicio


# ---------------- TomTom ----------------


@pytest.fixture
def _chave_tomtom(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RIOLIVE_TOMTOM_API_KEY", "chave-teste")
    from riolive.config import config

    config.cache_clear()


def test_tomtom_fora_da_janela_e_rodada_vazia(
    _chave_tomtom: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 03:30 da manhã: fora do pico e fora da rodada da hora cheia
    class RelogioFalso(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[no-untyped-def]
            return datetime(2026, 8, 6, 3, 30, tzinfo=tz)

    monkeypatch.setattr(transito_tomtom, "datetime", RelogioFalso)
    with ClienteHttp() as cliente:
        resultado = transito_tomtom.coletar(cliente)
    assert resultado.medicoes == [] and resultado.locais == []


def test_tomtom_no_pico_coleta_corredores(
    _chave_tomtom: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    class RelogioFalso(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[no-untyped-def]
            return datetime(2026, 8, 6, 8, 30, tzinfo=tz)

    monkeypatch.setattr(transito_tomtom, "datetime", RelogioFalso)
    corpo = {"flowSegmentData": {"currentSpeed": 29, "freeFlowSpeed": 38, "confidence": 1.0}}
    with respx.mock:
        respx.get(url__startswith=transito_tomtom.URL).mock(
            return_value=httpx.Response(200, json=corpo)
        )
        with ClienteHttp() as cliente:
            resultado = transito_tomtom.coletar(cliente)
    assert len(resultado.locais) == len(transito_tomtom.CORREDORES)
    assert len(resultado.medicoes) == 2 * len(transito_tomtom.CORREDORES)
    aterro = [m for m in resultado.medicoes if m.codigo_local == "aterro"]
    assert {m.metrica for m in aterro} == {"vel_kmh", "vel_livre_kmh"}


def test_tomtom_sem_chave_e_defeito_nosso(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RIOLIVE_TOMTOM_API_KEY", "")
    from riolive.config import config

    config.cache_clear()
    with ClienteHttp() as cliente, pytest.raises(RuntimeError, match="TOMTOM"):
        transito_tomtom.coletar(cliente)


def _agora_utc() -> datetime:
    return datetime.now(tz=UTC)
