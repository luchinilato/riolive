"""Backfill de chuva do datario — o que dá errado em silêncio.

Sem banco e sem BigQuery: só a conversão de linha da origem em medição nossa,
que é onde mora o risco de erro que não aparece.
"""

from datetime import UTC, date, datetime, time

from riolive.fontes.comum import TZ_RIO
from riolive.semente.chuva_datario import _medicoes


class LinhaFalsa:
    """Imita a Row do BigQuery: acesso por atributo."""

    def __init__(
        self,
        id_estacao: str,
        data_particao: date,
        horario: time,
        m15: float | None,
        m1h: float | None,
    ) -> None:
        self.id_estacao = id_estacao
        self.data_particao = data_particao
        self.horario = horario
        self.acumulado_chuva_15_min = m15
        self.acumulado_chuva_1_h = m1h


LOCAIS = {"1": 10, "2": 20}


def test_horario_e_hora_do_rio_e_nao_utc() -> None:
    """A origem não declara fuso no `horario` — e o valor é hora local.

    Lido como UTC, toda a série histórica entra 3 h deslocada, o que joga as
    leituras da meia-noite para o dia anterior e desloca o total de todo dia 1
    e todo dia 31. É a mesma armadilha do `Z` mentiroso do SPPO, sem o rótulo
    para denunciar.
    """
    linha = LinhaFalsa("1", date(2003, 3, 15), time(2, 30), 1.2, 4.8)
    medicoes, _ = _medicoes([linha], LOCAIS)

    instante = medicoes[0].ts
    assert instante.astimezone(TZ_RIO).hour == 2
    # 02:30 no Rio é 05:30 UTC. Se este assert virar 02:30 UTC, a série inteira
    # andou três horas para trás — e nada mais no sistema denuncia.
    assert instante.astimezone(UTC) == datetime(2003, 3, 15, 5, 30, tzinfo=UTC)


def test_valor_nulo_nao_vira_zero() -> None:
    """Nulo é "não mediu"; zero é "mediu e não choveu".

    Trocar um pelo outro afunda a média histórica sem que nada acuse: os dias
    sem leitura entrariam como dias secos.
    """
    linha = LinhaFalsa("1", date(2003, 3, 15), time(2, 30), None, 4.8)
    metricas = {m.metrica for m in _medicoes([linha], LOCAIS)[0]}
    assert metricas == {"chuva_1h"}


def test_estacao_fora_da_rede_atual_e_descartada() -> None:
    """O backfill escreve nas estações que a coleta ao vivo já usa.

    Criar local novo aqui penduraria a série histórica em locais paralelos aos
    do presente, e o painel compararia duas redes diferentes achando que é uma.
    """
    linhas = [
        LinhaFalsa("1", date(2003, 3, 15), time(2, 30), 1.0, 2.0),
        LinhaFalsa("99", date(2003, 3, 15), time(2, 30), 1.0, 2.0),
    ]
    assert {m.codigo_local for m in _medicoes(linhas, LOCAIS)[0]} == {"1"}


def test_linha_sem_horario_e_descartada_e_contada() -> None:
    """A origem tem 7.178 linhas com `horario` nulo em 29,3 milhões.

    Uma delas derrubou o backfill em pleno voo, no mês 301 de 330. Sem hora não
    há instante, e medição sem instante não existe numa série temporal — mas o
    descarte precisa ser contado, senão vira buraco invisível na climatologia.
    """
    linhas = [
        LinhaFalsa("1", date(2023, 1, 5), None, 1.0, 2.0),  # type: ignore[arg-type]
        LinhaFalsa("1", date(2023, 1, 5), time(3, 0), 1.0, 2.0),
    ]
    medicoes, descartadas = _medicoes(linhas, LOCAIS)
    assert descartadas == 1
    assert len(medicoes) == 2  # só a linha boa, com suas duas métricas
