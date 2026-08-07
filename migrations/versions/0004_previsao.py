"""Tabela de previsão: a 4ª natureza de dado, decidida em 2026-08-06.

Previsão não é medição (é palpite sobre o futuro, e muda a cada rodada do
modelo): tabela própria guardando TODAS as rodadas (decisão A), com
`emitida_em` na chave. O painel lê só a view vw_previsao_atual (rodada mais
recente por instante-alvo); o histórico fica pra previsto × ocorrido.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-06
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "previsao",
        sa.Column("emitida_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("local_id", sa.Integer, sa.ForeignKey("local.id"), nullable=False),
        sa.Column("metrica", sa.String(32), nullable=False),
        sa.Column("ts_alvo", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valor", sa.Double, nullable=False),
        sa.Column("payload", JSONB),
        sa.PrimaryKeyConstraint("local_id", "metrica", "ts_alvo", "emitida_em"),
    )
    op.execute(
        "SELECT create_hypertable('previsao', 'emitida_em', "
        "chunk_time_interval => INTERVAL '1 month')"
    )
    op.execute(
        "ALTER TABLE previsao SET (timescaledb.compress, "
        "timescaledb.compress_segmentby = 'local_id, metrica', "
        "timescaledb.compress_orderby = 'emitida_em, ts_alvo')"
    )
    op.execute("SELECT add_compression_policy('previsao', INTERVAL '7 days')")

    op.execute(
        """
        CREATE VIEW vw_previsao_atual AS
        SELECT DISTINCT ON (local_id, metrica, ts_alvo)
               local_id, metrica, ts_alvo, valor, emitida_em
        FROM previsao
        WHERE emitida_em > now() - interval '2 days'
        ORDER BY local_id, metrica, ts_alvo, emitida_em DESC
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_previsao_atual")
    op.drop_table("previsao")
