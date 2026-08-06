"""Agregados contínuos: a Tese 2 (memória) virando feature de banco.

- medicao_1h / medicao_1d: base de toda consulta histórica.
- frota_veiculo_15min + view frota_linha_15min: veículos ativos e velocidade média por
  linha (contagem distinta não é suportada em agregado contínuo; agregamos por veículo
  e a view conta em cima).
- uptime_fonte_1d: transparência histórica da status page.
- climatologia: fica pra fase do backfill (materializada mensal comum, precisa do
  histórico desde 2016 pra fazer sentido).

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-06
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# CREATE MATERIALIZED VIEW ... WITH (timescaledb.continuous) não roda em transação
AGREGADOS = {
    "medicao_1h": """
        CREATE MATERIALIZED VIEW medicao_1h
        WITH (timescaledb.continuous) AS
        SELECT time_bucket('1 hour', ts) AS bucket,
               local_id, metrica,
               avg(valor) AS media, min(valor) AS minimo, max(valor) AS maximo,
               count(*) AS n
        FROM medicao
        GROUP BY bucket, local_id, metrica
        WITH NO DATA
    """,
    "medicao_1d": """
        CREATE MATERIALIZED VIEW medicao_1d
        WITH (timescaledb.continuous) AS
        SELECT time_bucket('1 day', ts) AS bucket,
               local_id, metrica,
               avg(valor) AS media, min(valor) AS minimo, max(valor) AS maximo,
               count(*) AS n
        FROM medicao
        GROUP BY bucket, local_id, metrica
        WITH NO DATA
    """,
    "frota_veiculo_15min": """
        CREATE MATERIALIZED VIEW frota_veiculo_15min
        WITH (timescaledb.continuous) AS
        SELECT time_bucket('15 minutes', ts) AS bucket,
               modal, linha, veiculo_id,
               avg(velocidade) AS vel_media, count(*) AS n_posicoes
        FROM posicao
        GROUP BY bucket, modal, linha, veiculo_id
        WITH NO DATA
    """,
    "uptime_fonte_1d": """
        CREATE MATERIALIZED VIEW uptime_fonte_1d
        WITH (timescaledb.continuous) AS
        SELECT time_bucket('1 day', ts) AS bucket,
               fonte_id,
               count(*) AS transicoes,
               count(*) FILTER (WHERE estado <> 'online') AS transicoes_problema
        FROM saude_fonte
        GROUP BY bucket, fonte_id
        WITH NO DATA
    """,
}

POLITICAS = [
    # (agregado, start_offset, end_offset, cadência de refresh)
    ("medicao_1h", "'3 days'", "'1 hour'", "'30 minutes'"),
    ("medicao_1d", "'7 days'", "'1 day'", "'6 hours'"),
    ("frota_veiculo_15min", "'6 hours'", "'15 minutes'", "'15 minutes'"),
    ("uptime_fonte_1d", "'7 days'", "'1 day'", "'6 hours'"),
]


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for sql in AGREGADOS.values():
            op.execute(sql)
        for nome, inicio, fim, cadencia in POLITICAS:
            op.execute(
                f"SELECT add_continuous_aggregate_policy('{nome}', "
                f"start_offset => INTERVAL {inicio}, "
                f"end_offset => INTERVAL {fim}, "
                f"schedule_interval => INTERVAL {cadencia})"
            )

    # Planejado x realizado e detector de linha parada consultam por aqui
    op.execute(
        """
        CREATE VIEW frota_linha_15min AS
        SELECT bucket, modal, linha,
               count(*) AS veiculos_ativos,
               avg(vel_media) AS vel_media
        FROM frota_veiculo_15min
        GROUP BY bucket, modal, linha
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS frota_linha_15min")
    with op.get_context().autocommit_block():
        for nome in AGREGADOS:
            op.execute(f"DROP MATERIALIZED VIEW IF EXISTS {nome}")
