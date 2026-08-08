"""A soma de chuva conta cada janela uma vez só — e conta todas as estações.

`chuva_15min` é uma **janela móvel de 15 minutos**, e a frequência com que a
origem a publica mudou no meio da série: de 15 em 15 min até fevereiro de 2024,
de 5 em 5 min depois. Somar toda leitura contava a mesma chuva três vezes.

O primeiro conserto (0007) escolhia a leitura na marca do relógio, e trocou um
defeito por outro: no histórico cada estação publica na fase dela, então 23 das
26 estações de 1997 sumiam da climatologia sem erro nenhum. A 0008 escolhe uma
leitura por janela de cada estação, que é o critério que não depende do relógio.

Os dois testes são a rede: um trava a contagem repetida, o outro trava a perda
de estação. O segundo é o que teria pegado a 0007.
"""

import pytest
from sqlalchemy import text

from riolive.db import sessao


def _banco_disponivel() -> bool:
    try:
        with sessao() as s:
            s.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _banco_disponivel(), reason="Postgres do compose fora do ar")


def test_diario_soma_o_agregado_de_janela() -> None:
    """A dedup tem que estar na definição, não na consulta.

    Se ficasse na rota, qualquer outro consumidor do `chuva_dia_estacao` somaria
    errado sem saber — e o agregado existe justamente para ser a base somável.
    """
    with sessao() as s:
        definicoes = dict(
            s.execute(
                text(
                    "SELECT view_name, view_definition "
                    "FROM timescaledb_information.continuous_aggregates "
                    "WHERE view_name IN ('chuva_dia_estacao', 'chuva_15min_estacao')"
                )
            ).all()
        )

    assert "chuva_15min_estacao" in definicoes, "o agregado de janela não existe"
    janela = " ".join(definicoes["chuva_15min_estacao"].split()).lower()
    assert "first(" in janela, janela
    assert "'15 min" in janela or "'00:15:00'" in janela, janela

    diario = " ".join(definicoes["chuva_dia_estacao"].split()).lower()
    assert "chuva_15min_estacao" in diario, diario
    assert "% 15" not in diario, "voltou a escolher leitura pelo relógio: " + diario


def test_nenhum_ano_conta_mais_de_uma_leitura_por_janela() -> None:
    """96 leituras por dia é o teto físico: 24 h dividida em janelas de 15 min.

    Passar disso significa que a mesma janela entrou mais de uma vez — que é
    exatamente o defeito, medido em dado real em vez de em fixture.
    """
    with sessao() as s:
        piores = s.execute(
            text(
                "SELECT EXTRACT(YEAR FROM dia)::int ano, round(avg(leituras), 1) media "
                "FROM chuva_dia_estacao GROUP BY 1 HAVING avg(leituras) > 96.5 ORDER BY 2 DESC"
            )
        ).all()
    assert not piores, f"anos contando janela repetida: {[(p.ano, float(p.media)) for p in piores]}"


def test_agregado_nao_perde_estacao_do_dado_bruto() -> None:
    """Estação que mediu tem que aparecer na climatologia.

    A 0007 mantinha as 33 de hoje e deixava 3 de 1997 — a comparação virava
    "média de três pluviômetros" contra "média da rede", sem nada em tela
    dizendo isso. Comparado ano a ano contra o próprio bruto, sem número fixo:
    quantas estações existiam em cada ano é dado, não constante de teste.
    """
    with sessao() as s:
        divergentes = s.execute(
            text(
                """
                WITH bruto AS (
                    SELECT EXTRACT(YEAR FROM ts AT TIME ZONE 'America/Sao_Paulo')::int AS ano,
                           count(DISTINCT local_id) AS estacoes
                    FROM medicao WHERE metrica = 'chuva_15min' GROUP BY 1
                ), agregado AS (
                    SELECT EXTRACT(YEAR FROM dia)::int AS ano,
                           count(DISTINCT local_id) AS estacoes
                    FROM chuva_dia_estacao GROUP BY 1
                )
                SELECT b.ano, b.estacoes AS no_bruto, coalesce(a.estacoes, 0) AS no_agregado
                FROM bruto b LEFT JOIN agregado a USING (ano)
                WHERE coalesce(a.estacoes, 0) < b.estacoes
                ORDER BY b.ano
                """
            )
        ).all()
    assert not divergentes, "anos perdendo estação no agregado: " + str(
        [(d.ano, d.no_bruto, d.no_agregado) for d in divergentes]
    )
