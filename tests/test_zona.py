"""Recorte por zona popular nas rotas de leitura.

O seletor de zona do painel esteve no ar prometendo um recorte que nenhuma rota
sabia fazer — escolher uma zona devolvia o painel de demonstração inteiro. Estes
testes travam o que faltava: que o filtro filtre, que particione (a soma das
quatro zonas é a cidade) e que zona escrita errada seja recusada em vez de virar
lista vazia, que o painel desenharia como "não há estação aqui".
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from riolive.api.aplicacao import app

ZONAS = ("centro", "sul", "norte", "oeste")


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


@pytest.mark.parametrize("rota", ["/chuva/estacoes", "/ar/estacoes", "/eventos"])
def test_zona_invalida_e_recusada(cliente: TestClient, rota: str) -> None:
    """422 com a lista de valores, nunca 200 com lista vazia.

    Vazio silencioso é indistinguível de "não há dado nesta zona" — o painel
    desenharia a ausência como fato.
    """
    resposta = cliente.get(rota, params={"zona": "zona norte"})
    assert resposta.status_code == 422, resposta.text


@pytest.mark.parametrize("rota", ["/chuva/estacoes", "/ar/estacoes"])
def test_estacoes_da_zona_sao_da_zona(cliente: TestClient, rota: str) -> None:
    for zona in ZONAS:
        estacoes = cliente.get(rota, params={"zona": zona}).json()
        assert all(e["zona"] == zona for e in estacoes), (rota, zona, estacoes)


def test_as_quatro_zonas_particionam_a_rede_de_chuva(cliente: TestClient) -> None:
    """Os 33 pluviômetros têm RA resolvida, então zona nenhuma pode sumir com um.

    Se a soma das partes for menor que o todo, alguma estação caiu num buraco do
    mapeamento — que é o defeito que a trava da 0006 existe para evitar e que
    aqui é medido pelo lado de fora.
    """
    cidade = {e["id"] for e in cliente.get("/chuva/estacoes").json()}
    das_zonas: set[int] = set()
    for zona in ZONAS:
        das_zonas |= {e["id"] for e in cliente.get("/chuva/estacoes", params={"zona": zona}).json()}
    assert das_zonas == cidade, f"estações fora de toda zona: {cidade - das_zonas}"


def test_climatologia_recorta_os_dois_lados_da_comparacao(cliente: TestClient) -> None:
    """Filtrar só o ano corrente compararia a zona de hoje com a cidade de 1997.

    O recorte entra antes da média, então TODO ano da série tem que encolher —
    é isso que o teste mede, ano a ano, sem depender de quantas estações a zona
    tem hoje.
    """
    cidade = cliente.get("/chuva/climatologia").json()
    zona = cliente.get("/chuva/climatologia", params={"zona": "sul"}).json()

    assert zona["zona"] == "sul"
    assert "Zona Sul" in zona["metodologia"]

    por_ano = {p["ano"]: p["estacoes"] for p in cidade["serie"]}
    assert por_ano, "série da cidade vazia: banco sem histórico de chuva"
    for ponto in zona["serie"]:
        assert ponto["estacoes"] < por_ano[ponto["ano"]], (ponto, por_ano[ponto["ano"]])


def test_seguranca_recorta_a_memoria_junto_com_a_janela(cliente: TestClient) -> None:
    """`por_ano` é a memória da cidade e também tem que respeitar a zona.

    Recortar só a janela mostraria 42 tiroteios na Zona Sul contra a história de
    28 mil da cidade — a comparação que dá o susto errado. E sem zona pedida
    nada pode mudar: os 5 tiroteios sem RA resolvida continuam contando, que é a
    diferença entre a soma das quatro zonas e o total.
    """
    cidade = cliente.get("/seguranca/resumo", params={"horas": 24 * 365}).json()
    total_cidade = sum(a["ocorrencias"] for a in cidade["por_ano"])
    assert total_cidade > 0, "banco sem histórico de tiroteio"

    soma = 0
    for zona in ZONAS:
        recorte = cliente.get("/seguranca/resumo", params={"horas": 24 * 365, "zona": zona}).json()
        assert recorte["zona"] == zona
        assert recorte["ocorrencias"] <= cidade["ocorrencias"]
        soma += sum(a["ocorrencias"] for a in recorte["por_ano"])

    sem_ra = total_cidade - soma
    assert 0 <= sem_ra, f"zonas somam mais que a cidade: {soma} > {total_cidade}"
    # Folga curta: ocorrência sem RA é exceção da origem, não regra. Se virar
    # regra, o recorte territorial passa a esconder cidade e isto tem que gritar.
    assert sem_ra < total_cidade * 0.01, f"{sem_ra} ocorrências sem RA de {total_cidade}"


def test_eventos_da_zona_sao_da_zona(cliente: TestClient) -> None:
    for zona in ZONAS:
        eventos = cliente.get("/eventos", params={"zona": zona, "horas": 24 * 30}).json()
        assert all(e["zona"] == zona for e in eventos), (zona, eventos[:3])
