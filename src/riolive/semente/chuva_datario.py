"""Backfill de chuva do datalake `datario` (BigQuery) — a Tese 2 ganhando lastro.

Traz 1997 até 2024-06 das mesmas 33 estações do Alerta Rio que a gente lê ao
vivo, e é isso que permite dizer "choveu mais em 3 horas do que a média de
agosto inteiro" no instante em que acontece, em vez de só meses depois do
lançamento.

Cobertura medida na origem antes de escrever isto: 95% a 100% em todos os 27
anos, sem buraco. A rede cresceu de 26 estações (1997) para 33 (a partir de
2013) — a comparação segue legítima (é a chuva da cidade pela rede vigente),
mas a metodologia tem que dizer isso em vez de sugerir rede constante.

## Duas escolhas que valem explicação

**Só `chuva_15min` e `chuva_1h`.** A origem traz cinco acumulados (15 min, 1 h,
4 h, 24 h, 96 h) e importar todos daria 146 milhões de linhas em vez de 58,7.
O de 15 min é a base somável e o de 1 h é a régua que o Alerta Rio publica (e
que o painel usa); os demais são acumulados móveis deriváveis da base.

**Somar `chuva_1h` de todas as leituras dá 4× a chuva real** — as leituras são
de 15 em 15 minutos e o acumulado é móvel. Quem for calcular climatologia usa a
série de 15 min, ou amostra a de 1 h de hora em hora. Registrado aqui porque é
um erro que não aparece: infla a "média histórica" em quatro vezes e ninguém
percebe.

Uso: `python -m riolive.semente.chuva_datario [--ano-inicial 1997] [--teto-gb 50]`
Re-executar é seguro: a PK natural (local_id, metrica, ts) deduplica, e mês já
preenchido é pulado antes de gastar byte de consulta.
"""

import argparse
import logging
from datetime import UTC, date, datetime
from typing import Any

from google.cloud import bigquery
from sqlalchemy import text

from riolive.db import sessao
from riolive.fontes.comum import TZ_RIO
from riolive.ingestao.contrato import MedicaoNova
from riolive.ingestao.gravacao import agora_utc, inserir_medicoes

logger = logging.getLogger(__name__)

TABELA = "datario.clima_pluviometro.taxa_precipitacao_alertario"
SLUG_FONTE = "alerta_rio"

# (coluna na origem, métrica nossa)
METRICAS = (("acumulado_chuva_15_min", "chuva_15min"), ("acumulado_chuva_1_h", "chuva_1h"))

ANO_INICIAL = 1997
FIM_DA_SERIE = date(2024, 6, 30)  # a origem parou de ser alimentada em 2024-06-03
TETO_GB_PADRAO = 50.0  # trava contra varredura indisciplinada do free tier (1 TB/mês)


def _fonte_e_locais() -> tuple[int, dict[str, int]]:
    """Id da fonte e mapa codigo_externo → local_id. O backfill não cria local:
    escreve nas mesmas estações que a coleta ao vivo já usa, senão a série
    histórica ficaria pendurada em locais paralelos aos do presente."""
    with sessao() as s:
        fonte_id = s.execute(
            text("SELECT id FROM fonte WHERE slug = :slug"), {"slug": SLUG_FONTE}
        ).scalar_one()
        locais = {
            linha.codigo_externo: linha.id
            for linha in s.execute(
                text("SELECT id, codigo_externo FROM local WHERE fonte_id = :f"), {"f": fonte_id}
            ).all()
        }
    return fonte_id, locais


def _meses_pendentes(fonte_id: int, ano_inicial: int) -> list[tuple[date, date]]:
    """Meses do intervalo que ainda não têm medição nossa.

    Pular antes de consultar é o que segura o custo: mês já carregado não gasta
    byte de BigQuery, então re-executar depois de uma queda custa quase nada.
    """
    with sessao() as s:
        preenchidos = {
            linha.mes
            for linha in s.execute(
                text(
                    "SELECT DISTINCT date_trunc('month', ts)::date AS mes FROM medicao "
                    "WHERE fonte_id = :f AND metrica = 'chuva_15min' AND ts < :fim"
                ),
                {"f": fonte_id, "fim": datetime(2025, 1, 1, tzinfo=UTC)},
            ).all()
        }
    pendentes = []
    for ano in range(ano_inicial, FIM_DA_SERIE.year + 1):
        for mes in range(1, 13):
            inicio = date(ano, mes, 1)
            if inicio > FIM_DA_SERIE:
                break
            fim = date(ano + (mes == 12), (mes % 12) + 1, 1)
            if inicio not in preenchidos:
                pendentes.append((inicio, fim))
    return pendentes


def _consultar(cliente: bigquery.Client, inicio: date, fim: date) -> tuple[list[Any], float]:
    """Lê um mês. Devolve (linhas, GB escaneados) — o custo volta junto porque
    varredura sem contador é como a origem some do free tier sem aviso."""
    colunas = ", ".join(coluna for coluna, _ in METRICAS)
    sql = f"""
        SELECT id_estacao, horario, data_particao, {colunas}
        FROM `{TABELA}`
        WHERE data_particao >= @inicio AND data_particao < @fim
    """  # noqa: S608 - nomes de coluna são constantes do módulo, não entrada externa
    parametros = [
        bigquery.ScalarQueryParameter("inicio", "DATE", inicio),
        bigquery.ScalarQueryParameter("fim", "DATE", fim),
    ]
    seco = cliente.query(
        sql, job_config=bigquery.QueryJobConfig(dry_run=True, query_parameters=parametros)
    )
    gb = (seco.total_bytes_processed or 0) / 1e9
    linhas = cliente.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=parametros))
    return list(linhas.result()), gb


def _medicoes(linhas: list[Any], locais: dict[str, int]) -> list[MedicaoNova]:
    saida: list[MedicaoNova] = []
    for linha in linhas:
        codigo = str(linha.id_estacao)
        if codigo not in locais:
            continue  # estação que não existe na nossa rede atual
        # `horario` vem como hora local do Rio, sem fuso declarado
        instante = datetime.combine(linha.data_particao, linha.horario).replace(tzinfo=TZ_RIO)
        for coluna, metrica in METRICAS:
            valor = getattr(linha, coluna)
            if valor is None:
                continue
            saida.append(
                MedicaoNova(codigo_local=codigo, metrica=metrica, ts=instante, valor=float(valor))
            )
    return saida


def _materializar() -> None:
    """Refaz o agregado de chuva diária sobre o passado recém-escrito.

    A política de refresh só olha os últimos 7 dias, então dado de 1997 entra na
    `medicao` e o agregado segue sem enxergar — a climatologia continuaria vazia
    depois de um backfill que funcionou. Precisa de autocommit: `CALL
    refresh_continuous_aggregate` não roda dentro de transação.
    """
    from riolive.db import engine

    with engine().connect().execution_options(isolation_level="AUTOCOMMIT") as c:
        c.execute(text("CALL refresh_continuous_aggregate('chuva_dia_estacao', NULL, NULL)"))
    logger.info("agregado chuva_dia_estacao materializado")


def rodar(ano_inicial: int = ANO_INICIAL, teto_gb: float = TETO_GB_PADRAO) -> dict[str, float]:
    from riolive.config import config

    cliente = bigquery.Client(project=config().gcp_projeto)
    fonte_id, locais = _fonte_e_locais()
    pendentes = _meses_pendentes(fonte_id, ano_inicial)
    logger.info("%s meses pendentes (%s estações na rede atual)", len(pendentes), len(locais))

    total = {"meses": 0, "inseridos": 0, "gb": 0.0}
    for inicio, fim in pendentes:
        if total["gb"] >= teto_gb:
            logger.warning("teto de %.0f GB atingido — parando em %s", teto_gb, inicio)
            break
        linhas, gb = _consultar(cliente, inicio, fim)
        total["gb"] += gb
        medicoes = _medicoes(linhas, locais)
        with sessao() as s:
            inseridos = inserir_medicoes(s, fonte_id, medicoes, locais, agora_utc())
            s.commit()
        total["meses"] += 1
        total["inseridos"] += inseridos
        logger.info(
            "%s: %s leituras → %s medições novas (%.2f GB · acumulado %.1f GB)",
            inicio,
            len(linhas),
            inseridos,
            gb,
            total["gb"],
        )
    if total["inseridos"]:
        _materializar()
    return total


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="Backfill de chuva do datario (BigQuery)")
    p.add_argument("--ano-inicial", type=int, default=ANO_INICIAL)
    p.add_argument("--teto-gb", type=float, default=TETO_GB_PADRAO)
    args = p.parse_args()
    resultado = rodar(ano_inicial=args.ano_inicial, teto_gb=args.teto_gb)
    logger.info("fim: %s", resultado)


if __name__ == "__main__":
    main()
