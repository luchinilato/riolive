"""Dimensões GTFS: o "planejado" da Tese 3 (planejado × realizado).

Carregadas do zip mensal da SMTR (ArcGIS item 8ffe62ad3b2f42e49814bf941654ea6c,
CC-BY 4.0) pelo seed riolive.semente.gtfs — que trunca e recarrega tudo.
Horários GTFS passam de meia-noite ("25:30:00"): guardados como segundos.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-06
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

TABELAS = [
    "gtfs_feed",
    "gtfs_calendar_dates",
    "gtfs_calendar",
    "gtfs_frequencies",
    "gtfs_stop_times",
    "gtfs_shapes",
    "gtfs_stops",
    "gtfs_trips",
    "gtfs_routes",
]


def upgrade() -> None:
    op.create_table(
        "gtfs_routes",
        sa.Column("route_id", sa.Text, primary_key=True),
        sa.Column("agency_id", sa.Text),
        sa.Column("short_name", sa.Text),
        sa.Column("long_name", sa.Text),
        sa.Column("route_type", sa.SmallInteger),
    )
    op.create_table(
        "gtfs_trips",
        sa.Column("trip_id", sa.Text, primary_key=True),
        sa.Column("route_id", sa.Text, nullable=False),
        sa.Column("service_id", sa.Text, nullable=False),
        sa.Column("headsign", sa.Text),
        sa.Column("direction_id", sa.SmallInteger),
        sa.Column("shape_id", sa.Text),
    )
    op.create_index("ix_gtfs_trips_route", "gtfs_trips", ["route_id"])
    op.create_table(
        "gtfs_stops",
        sa.Column("stop_id", sa.Text, primary_key=True),
        sa.Column("nome", sa.Text),
        sa.Column("lat", sa.Double),
        sa.Column("lon", sa.Double),
    )
    op.create_table(
        "gtfs_shapes",
        sa.Column("shape_id", sa.Text, nullable=False),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("lat", sa.Double, nullable=False),
        sa.Column("lon", sa.Double, nullable=False),
        sa.PrimaryKeyConstraint("shape_id", "seq"),
    )
    op.create_table(
        "gtfs_stop_times",
        sa.Column("trip_id", sa.Text, nullable=False),
        sa.Column("stop_sequence", sa.Integer, nullable=False),
        sa.Column("stop_id", sa.Text, nullable=False),
        sa.Column("chegada_seg", sa.Integer),  # segundos desde meia-noite; >86400 = dia seguinte
        sa.Column("partida_seg", sa.Integer),
        sa.PrimaryKeyConstraint("trip_id", "stop_sequence"),
    )
    op.create_index("ix_gtfs_stop_times_stop", "gtfs_stop_times", ["stop_id"])
    op.create_table(
        "gtfs_frequencies",
        sa.Column("trip_id", sa.Text, nullable=False),
        sa.Column("inicio_seg", sa.Integer, nullable=False),
        sa.Column("fim_seg", sa.Integer, nullable=False),
        sa.Column("headway_seg", sa.Integer, nullable=False),
        sa.Column("exact_times", sa.SmallInteger),
        sa.PrimaryKeyConstraint("trip_id", "inicio_seg"),
    )
    op.create_table(
        "gtfs_calendar",
        sa.Column("service_id", sa.Text, primary_key=True),
        sa.Column("dias", sa.SmallInteger, nullable=False),  # bitmask seg=1 ... dom=64
        sa.Column("inicio", sa.Date, nullable=False),
        sa.Column("fim", sa.Date, nullable=False),
    )
    op.create_table(
        "gtfs_calendar_dates",
        sa.Column("service_id", sa.Text, nullable=False),
        sa.Column("data", sa.Date, nullable=False),
        sa.Column("exception_type", sa.SmallInteger, nullable=False),  # 1 add, 2 remove
        sa.PrimaryKeyConstraint("service_id", "data"),
    )
    op.create_table(
        "gtfs_feed",
        sa.Column("carregado_em", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("feed_version", sa.Text),
        sa.Column("info", JSONB),
    )


def downgrade() -> None:
    for tabela in TABELAS:
        op.drop_table(tabela)
