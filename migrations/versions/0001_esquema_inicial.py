"""Esquema inicial: dimensões, fatos como hypertables, compressão, retenção e view pública.

Espec: DEC - Modelo de dados (2026-08-05 Modelo de dados - proposta v1).

Revision ID: 0001
Revises:
Create Date: 2026-08-06
"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    # ---------- Dimensões ----------
    op.create_table(
        "fonte",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("nome", sa.Text, nullable=False),
        sa.Column("orgao", sa.Text, nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("licenca", sa.Text),
        sa.Column("bloco", sa.String(1), nullable=False),
        sa.Column("criticidade", sa.SmallInteger, nullable=False),
        sa.Column("cadencia_segundos", sa.Integer, nullable=False),
    )
    op.create_table(
        "ra",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.Text, nullable=False),
    )
    op.create_table(
        "bairro",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.Text, nullable=False),
        sa.Column("ra_id", sa.Integer, sa.ForeignKey("ra.id")),
        sa.Column("populacao", sa.Integer),
        sa.Column("geom", Geometry("MULTIPOLYGON", srid=4326), nullable=False),
    )
    op.create_table(
        "local",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("fonte_id", sa.Integer, sa.ForeignKey("fonte.id"), nullable=False),
        sa.Column("codigo_externo", sa.String(64), nullable=False),
        sa.Column("nome", sa.Text, nullable=False),
        sa.Column("tipo", sa.String(32), nullable=False),
        sa.Column("geom", Geometry("POINT", srid=4326), nullable=False),
        sa.Column("bairro_id", sa.Integer, sa.ForeignKey("bairro.id")),
        sa.Column("ra_id", sa.Integer, sa.ForeignKey("ra.id")),
        sa.Column("h3_r8", sa.String(16)),
        sa.Column("extra", JSONB),
        sa.UniqueConstraint("fonte_id", "codigo_externo"),
    )

    # ---------- Fatos ----------
    op.create_table(
        "medicao",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("local_id", sa.Integer, sa.ForeignKey("local.id"), nullable=False),
        sa.Column("fonte_id", sa.Integer, sa.ForeignKey("fonte.id"), nullable=False),
        sa.Column("metrica", sa.String(32), nullable=False),
        sa.Column("valor", sa.Double, nullable=False),
        sa.Column("coletado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSONB),
        sa.PrimaryKeyConstraint("local_id", "metrica", "ts"),
    )
    op.create_table(
        "posicao",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("modal", sa.String(8), nullable=False),
        sa.Column("veiculo_id", sa.String(32), nullable=False),
        sa.Column("linha", sa.String(32)),
        sa.Column("geom", Geometry("POINT", srid=4326), nullable=False),
        sa.Column("velocidade", sa.SmallInteger),
        sa.Column("extra", JSONB),
        sa.Column("coletado_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("modal", "veiculo_id", "ts"),
        sa.CheckConstraint("modal IN ('onibus', 'brt', 'aviao', 'navio')"),
    )
    op.create_table(
        "evento",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("tipo", sa.String(32), nullable=False),
        sa.Column("fonte_id", sa.Integer, sa.ForeignKey("fonte.id"), nullable=False),
        sa.Column("severidade", sa.SmallInteger, nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fim", sa.DateTime(timezone=True)),
        sa.Column("titulo", sa.Text, nullable=False),
        sa.Column("descricao", sa.Text),
        sa.Column("geom", Geometry("POINT", srid=4326)),
        sa.Column("bairro_id", sa.Integer, sa.ForeignKey("bairro.id")),
        sa.Column("ra_id", sa.Integer, sa.ForeignKey("ra.id")),
        sa.Column("h3_r8", sa.String(16)),
        sa.Column("visivel_apos", sa.DateTime(timezone=True)),
        sa.Column("payload", JSONB),
        sa.Column("coletado_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("inicio", "id"),
        sa.CheckConstraint("severidade BETWEEN 1 AND 5"),
    )
    op.create_table(
        "snapshot_cidade",
        sa.Column("ts", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("ici", sa.Numeric),
        sa.Column("componentes", JSONB),
        sa.Column("contadores", JSONB),
        sa.Column("payload", JSONB),
    )
    op.create_table(
        "saude_fonte",
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fonte_id", sa.Integer, sa.ForeignKey("fonte.id"), nullable=False),
        sa.Column("estado", sa.String(16), nullable=False),
        sa.Column("classe_falha", sa.String(16)),
        sa.Column("latencia_ms", sa.Integer),
        sa.Column("detalhe", sa.Text),
        sa.PrimaryKeyConstraint("fonte_id", "ts"),
        sa.CheckConstraint("estado IN ('online', 'degradada', 'fora', 'congelada')"),
        sa.CheckConstraint("classe_falha IS NULL OR classe_falha IN ('rede', 'schema', 'frescor')"),
    )
    op.create_table(
        "blob_manifesto",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column("fonte_id", sa.Integer, sa.ForeignKey("fonte.id"), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("meta", JSONB),
    )

    # ---------- Hypertables ----------
    op.execute(
        "SELECT create_hypertable('medicao', 'ts', chunk_time_interval => INTERVAL '7 days')"
    )
    op.execute("SELECT create_hypertable('posicao', 'ts', chunk_time_interval => INTERVAL '1 day')")
    op.execute(
        "SELECT create_hypertable('evento', 'inicio', chunk_time_interval => INTERVAL '1 month')"
    )
    op.execute(
        "SELECT create_hypertable('snapshot_cidade', 'ts', "
        "chunk_time_interval => INTERVAL '1 month')"
    )
    op.execute(
        "SELECT create_hypertable('saude_fonte', 'ts', chunk_time_interval => INTERVAL '1 month')"
    )

    # ---------- Compressão e retenção (DEC: posições 90 dias; resto pra sempre) ----------
    op.execute(
        "ALTER TABLE medicao SET (timescaledb.compress, "
        "timescaledb.compress_segmentby = 'local_id, metrica', "
        "timescaledb.compress_orderby = 'ts')"
    )
    op.execute("SELECT add_compression_policy('medicao', INTERVAL '7 days')")

    op.execute(
        "ALTER TABLE posicao SET (timescaledb.compress, "
        "timescaledb.compress_segmentby = 'modal, linha', "
        "timescaledb.compress_orderby = 'ts')"
    )
    op.execute("SELECT add_compression_policy('posicao', INTERVAL '48 hours')")
    op.execute("SELECT add_retention_policy('posicao', INTERVAL '90 days')")

    # Eventos fecham (fim preenchido) muito antes de 90 dias; compressão tardia evita
    # reescrever chunk comprimido ao encerrar evento vigente
    op.execute(
        "ALTER TABLE evento SET (timescaledb.compress, "
        "timescaledb.compress_segmentby = 'tipo', "
        "timescaledb.compress_orderby = 'inicio')"
    )
    op.execute("SELECT add_compression_policy('evento', INTERVAL '90 days')")

    op.execute("ALTER TABLE snapshot_cidade SET (timescaledb.compress)")
    op.execute("SELECT add_compression_policy('snapshot_cidade', INTERVAL '30 days')")

    op.execute(
        "ALTER TABLE saude_fonte SET (timescaledb.compress, "
        "timescaledb.compress_segmentby = 'fonte_id', "
        "timescaledb.compress_orderby = 'ts')"
    )
    op.execute("SELECT add_compression_policy('saude_fonte', INTERVAL '30 days')")

    # ---------- Índices de consulta ----------
    op.create_index("ix_medicao_fonte_ts", "medicao", ["fonte_id", "ts"])
    op.create_index("ix_posicao_linha_ts", "posicao", ["linha", "ts"])
    op.create_index("ix_evento_tipo_inicio", "evento", ["tipo", "inicio"])
    op.create_index("ix_evento_bairro", "evento", ["bairro_id"])
    op.create_index("ix_evento_h3", "evento", ["h3_r8"])
    op.create_index(
        "ix_evento_vigente",
        "evento",
        ["tipo"],
        postgresql_where=sa.text("fim IS NULL"),
    )

    # ---------- Salvaguarda como esquema: API pública só lê por esta view ----------
    op.execute(
        """
        CREATE VIEW vw_evento_publico AS
        SELECT id, tipo, fonte_id, severidade, inicio, fim, titulo, descricao,
               geom, bairro_id, ra_id, h3_r8, coletado_em
        FROM evento
        WHERE visivel_apos IS NULL OR visivel_apos <= now()
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_evento_publico")
    for tabela in (
        "blob_manifesto",
        "saude_fonte",
        "snapshot_cidade",
        "evento",
        "posicao",
        "medicao",
        "local",
        "bairro",
        "ra",
        "fonte",
    ):
        op.drop_table(tabela)
