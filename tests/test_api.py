"""API de leitura contra o banco dev (compose). Pulados se o Postgres não estiver de pé."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from riolive.api.aplicacao import app


def _banco_disponivel() -> bool:
    try:
        from sqlalchemy import text

        from riolive.db import sessao

        with sessao() as s:
            s.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _banco_disponivel(), reason="Postgres do compose fora do ar")


@pytest.fixture
def cliente() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def test_agora_traz_estagio_e_frota(cliente: TestClient) -> None:
    corpo = cliente.get("/agora").json()
    assert corpo["estagio"]["severidade"] in range(1, 6)
    assert sum(corpo["veiculos_ativos"].values()) > 0  # algum modal vivo (fontes caem)


def test_fontes_lista_todas_com_estado(cliente: TestClient) -> None:
    corpo = cliente.get("/fontes").json()
    slugs = {f["slug"] for f in corpo}
    assert {"alerta_rio", "gps_sppo", "estagio_cor", "openaq"} <= slugs
    assert all(
        f["estado"] in ("online", "degradada", "fora", "congelada", "desconhecido") for f in corpo
    )  # "desconhecido" = fonte registrada sem transição ainda (ex. detector interno)


def test_eventos_vigentes_incluem_estagio(cliente: TestClient) -> None:
    corpo = cliente.get("/eventos", params={"vigentes": "true"}).json()
    assert any(e["tipo"] == "estagio_cor" and e["fim"] is None for e in corpo)


def test_posicoes_geojson_com_frota(cliente: TestClient) -> None:
    # Janela de 60 min e sem filtro de modal: o teste valida a mecânica do
    # endpoint, não a disponibilidade momentânea de uma fonte específica
    corpo = cliente.get("/posicoes", params={"minutos": 60}).json()
    assert corpo["type"] == "FeatureCollection"
    assert len(corpo["features"]) > 100
    ponto = corpo["features"][0]
    assert ponto["geometry"]["type"] == "Point"
    assert ponto["properties"]["modal"] in ("onibus", "brt", "aviao", "navio")
    veiculos = [p["properties"]["veiculo"] for p in corpo["features"]]
    assert len(veiculos) == len(set(veiculos))  # uma posição por veículo (a mais recente)


def test_series_1h_de_chuva(cliente: TestClient) -> None:
    corpo = cliente.get("/series/chuva_15min", params={"passo": "1h", "horas": 24}).json()
    assert corpo["metrica"] == "chuva_15min"
    assert isinstance(corpo["pontos"], list)


def test_serie_metrica_desconhecida_e_404(cliente: TestClient) -> None:
    assert cliente.get("/series/nao_existe").status_code == 404


def test_previsao_do_centro(cliente: TestClient) -> None:
    corpo = cliente.get("/previsao", params={"local": "centro", "horas": 12}).json()
    assert "temp_c" in corpo["metricas"]
    assert len(corpo["metricas"]["temp_c"]) > 0


def test_radar_manifesto_com_bounds_e_urls(cliente: TestClient) -> None:
    corpo = cliente.get("/radar", params={"quadros": 4}).json()
    assert corpo["bounds"] is not None
    assert 1 <= len(corpo["quadros"]) <= 4
    assert corpo["quadros"][0]["url"]  # pré-assinada (R2 configurado no dev)


def test_locais_estacoes_de_chuva(cliente: TestClient) -> None:
    corpo = cliente.get("/locais", params={"fonte": "alerta_rio"}).json()
    assert len(corpo["features"]) == 33
    assert corpo["features"][0]["properties"]["bairro"] is not None


def test_cache_control_pra_cdn(cliente: TestClient) -> None:
    resposta = cliente.get("/agora")
    assert "max-age" in resposta.headers["Cache-Control"]


def test_seguranca_resumo_traz_janela_e_memoria(cliente: TestClient) -> None:
    corpo = cliente.get("/seguranca/resumo", params={"horas": 24 * 30}).json()
    assert corpo["passo"] == "day"  # 30 dias em balde diário; hora seria ilegível
    assert corpo["ocorrencias"] >= 0
    assert corpo["mortos"] <= corpo["ocorrencias"] * 10  # sanidade grosseira da soma
    # o contexto de longo prazo não depende da janela: é a memória da cidade
    anos = {a["ano"] for a in corpo["por_ano"]}
    assert 2016 in anos, "backfill do Fogo Cruzado começa em 2016"
    pico = max(corpo["por_ano"], key=lambda a: a["ocorrencias"])
    assert pico["ano"] == 2018, "2018 foi o ano da intervenção federal — pico conhecido"


def test_seguranca_janela_curta_usa_balde_de_hora(cliente: TestClient) -> None:
    corpo = cliente.get("/seguranca/resumo", params={"horas": 24}).json()
    assert corpo["passo"] == "hour"


def test_ar_estacoes_lista_todas_mesmo_sem_leitura(cliente: TestClient) -> None:
    # Estação atrasada não pode sumir da lista: sumir sugere que ela não existe
    corpo = cliente.get("/ar/estacoes").json()
    assert len(corpo) == 28
    assert all("leituras" in e and "lat" in e and "lon" in e for e in corpo)


def test_eventos_trazem_nome_do_bairro(cliente: TestClient) -> None:
    # Sem o nome, quem consome usa o título pra dizer "onde" — e título de foco de
    # calor é o nome do satélite. O campo existe mesmo quando o evento não tem pino.
    corpo = cliente.get("/eventos", params={"horas": 24 * 7}).json()
    assert corpo, "esperava algum evento na última semana"
    assert all("bairro" in e and "ra" in e for e in corpo)
    com_bairro = [e for e in corpo if e["bairro_id"] is not None]
    assert all(e["bairro"] for e in com_bairro), "bairro_id preenchido tem que ter nome"


def test_ceu_aeronaves_com_serie_e_altitude(cliente: TestClient) -> None:
    corpo = cliente.get("/ceu/aeronaves", params={"minutos": 30}).json()
    assert corpo["total"] == len(corpo["aeronaves"])
    assert isinstance(corpo["serie_15min"], list)
    # altitude é número ou None; "ground" do adsb.lol não pode virar 0
    assert all(
        a["altitude_pes"] is None or isinstance(a["altitude_pes"], int) for a in corpo["aeronaves"]
    )


def test_queimadas_resumo_declara_desde_quando_temos_serie(cliente: TestClient) -> None:
    corpo = cliente.get("/queimadas/resumo", params={"horas": 24 * 30}).json()
    assert corpo["passo"] == "day"
    assert corpo["focos"] == sum(p["focos"] for p in corpo["serie"])
    assert corpo["focos"] >= len(corpo["lista"]) or len(corpo["lista"]) == 100
    # a memória do INPE aqui é curta e o dossiê precisa poder dizer desde quando
    assert "desde" in corpo
