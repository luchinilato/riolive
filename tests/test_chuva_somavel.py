"""A soma de chuva conta cada janela uma vez só.

`chuva_15min` é uma **janela móvel de 15 minutos**, e a frequência com que a
origem a publica mudou no meio da série: de 15 em 15 min até janeiro de 2024, de
5 em 5 min depois. Somar toda leitura contava a mesma chuva três vezes — fevereiro
de 2024 dava 324,7 mm por estação e o valor real é 107,3. A coleta ao vivo tem o
mesmo comportamento hoje, então o mês corrente entraria inflado contra um
histórico que não está, e o card anunciaria recorde de chuva o ano inteiro.
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


def test_agregado_filtra_pelas_marcas_de_15min() -> None:
    """O filtro tem que estar na definição do agregado, não na consulta.

    Se ficasse na rota, qualquer outro consumidor do `chuva_dia_estacao` somaria
    errado sem saber — e o agregado existe justamente para ser a base somável.
    """
    with sessao() as s:
        definicao = s.execute(
            text(
                "SELECT view_definition FROM timescaledb_information.continuous_aggregates "
                "WHERE view_name = 'chuva_dia_estacao'"
            )
        ).scalar_one()
    assert "15" in definicao
    normalizada = " ".join(definicao.split()).lower()
    assert "% 15" in normalizada or "mod" in normalizada, definicao


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
