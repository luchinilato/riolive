"""Chuva diária por estação em hora do Rio — a base da climatologia.

O `medicao_1d` de 0002 não serve para chuva por dois motivos:

1. **Bucket em UTC.** O dia dele começa às 21h do dia anterior no Rio. Para
   média de mês o desvio é pequeno, mas "choveu tanto no dia 7" com um dia que
   não é o dia 7 é o tipo de erro que ninguém audita e todo mundo repete.
2. **Guarda média, não soma.** Chuva se acumula. `media * n` reconstrói a soma,
   mas só enquanto ninguém mexer na cadência da fonte.

Este agregado responde a pergunta certa direto: quantos milímetros choveram na
estação X no dia Y, dia do calendário do Rio.

**Só `chuva_15min`.** É o único acumulado somável da fonte — os de 1 h, 4 h e
24 h são janelas móveis, e somá-los multiplica a chuva (o de 1 h por 4, já que a
leitura é de 15 em 15 minutos). Ver `semente/chuva_datario.py`.

Depois de um backfill histórico, materializar o passado à mão — a política de
refresh só olha os últimos 7 dias:

    CALL refresh_continuous_aggregate('chuva_dia_estacao', '1996-12-01', NULL);

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-07
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

AGREGADO = """
    CREATE MATERIALIZED VIEW chuva_dia_estacao
    WITH (timescaledb.continuous) AS
    SELECT time_bucket('1 day', ts, 'America/Sao_Paulo') AS dia,
           local_id,
           sum(valor) AS mm,
           count(*) AS leituras
    FROM medicao
    WHERE metrica = 'chuva_15min'
    GROUP BY dia, local_id
    WITH NO DATA
"""


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(AGREGADO)
        # Janela curta e refresh de hora em hora: o dia corrente é o que muda.
        op.execute(
            "SELECT add_continuous_aggregate_policy('chuva_dia_estacao', "
            "start_offset => INTERVAL '7 days', "
            "end_offset => INTERVAL '1 hour', "
            "schedule_interval => INTERVAL '1 hour')"
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP MATERIALIZED VIEW IF EXISTS chuva_dia_estacao")
