"""Soma diária de chuva usa só as marcas de 15 min.

O agregado de 0005 soma toda leitura de `chuva_15min`, e isso estava errado: o
campo é uma **janela móvel de 15 minutos**, e a origem mudou a frequência com
que a publica. Enquanto publicou de 15 em 15 minutos, somar tudo dava a chuva
certa por coincidência de alinhamento. A partir de fevereiro de 2024 ela passou
a publicar de 5 em 5 minutos, e a mesma chuva passou a ser contada três vezes.

Medido na origem para fevereiro de 2024: somando todas as leituras, 10.715 mm;
somando só as marcas de 15 min, 3.540 mm. Fator 3,03 — que é 15/5.

**A coleta ao vivo tem o mesmo comportamento hoje**: 2.437 de 3.636 leituras dos
últimos dias caem fora das marcas. Sem esta correção, o mês corrente entraria
inflado na climatologia e o histórico antigo não — o card anunciaria recorde de
chuva o ano inteiro.

A correção é escolher uma leitura por janela: a da marca (minuto múltiplo de
15), que é a única que fecha o intervalo sem sobrepor a vizinha. Leitura
intermediária é descartada por ser janela sobreposta, não por ser ruim.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-07
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

NOVO = """
    CREATE MATERIALIZED VIEW chuva_dia_estacao
    WITH (timescaledb.continuous) AS
    SELECT time_bucket('1 day', ts, 'America/Sao_Paulo') AS dia,
           local_id,
           sum(valor) AS mm,
           count(*) AS leituras
    FROM medicao
    WHERE metrica = 'chuva_15min'
      AND EXTRACT(MINUTE FROM ts)::int % 15 = 0
    GROUP BY dia, local_id
    WITH NO DATA
"""

ANTIGO = NOVO.replace("\n      AND EXTRACT(MINUTE FROM ts)::int % 15 = 0", "")

POLITICA = (
    "SELECT add_continuous_aggregate_policy('chuva_dia_estacao', "
    "start_offset => INTERVAL '7 days', "
    "end_offset => INTERVAL '1 hour', "
    "schedule_interval => INTERVAL '1 hour')"
)


def _recriar(definicao: str) -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP MATERIALIZED VIEW IF EXISTS chuva_dia_estacao")
        op.execute(definicao)
        op.execute(POLITICA)
        # Recriar zera a materialização: sem isto o agregado nasce vazio e a
        # climatologia responde "sem histórico" com o banco cheio.
        op.execute("CALL refresh_continuous_aggregate('chuva_dia_estacao', NULL, NULL)")


def upgrade() -> None:
    _recriar(NOVO)


def downgrade() -> None:
    _recriar(ANTIGO)
