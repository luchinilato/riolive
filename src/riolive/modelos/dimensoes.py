"""Dimensões: fonte, ra, bairro, local.

Alimentam crédito obrigatório nos painéis, health check, página de status,
normalização por 100 mil e os filtros da UI (bairro/RA).
"""

from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from riolive.modelos.base import Base


class Fonte(Base):
    __tablename__ = "fonte"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    nome: Mapped[str] = mapped_column(Text)
    orgao: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    licenca: Mapped[str | None] = mapped_column(Text)
    bloco: Mapped[str] = mapped_column(
        String(1)
    )  # A clima | B mobilidade | C segurança | D cidade | E histórico
    criticidade: Mapped[int] = mapped_column(SmallInteger)  # 1 a 5; pesa na priorização da home
    cadencia_segundos: Mapped[int] = mapped_column(
        Integer
    )  # cadência esperada de atualização do dado


class RA(Base):
    """Região administrativa (~34)."""

    __tablename__ = "ra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # codra do data.rio
    nome: Mapped[str] = mapped_column(Text)


class Bairro(Base):
    """~160 bairros, geometria do data.rio; espinha da normalização por 100 mil."""

    __tablename__ = "bairro"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # codbairro do data.rio
    nome: Mapped[str] = mapped_column(Text)
    ra_id: Mapped[int | None] = mapped_column(ForeignKey("ra.id"))
    populacao: Mapped[int | None] = mapped_column(Integer)
    geom: Mapped[object] = mapped_column(Geometry("MULTIPOLYGON", srid=4326))


class Local(Base):
    """Estações e pontos fixos: pluviômetro, estação de ar/rio, corredor, praia.

    Enriquecimento espacial (bairro/RA/H3) resolvido uma vez, na carga — nunca em query.
    """

    __tablename__ = "local"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fonte_id: Mapped[int] = mapped_column(ForeignKey("fonte.id"))
    codigo_externo: Mapped[str] = mapped_column(String(64))  # id da estação na fonte
    nome: Mapped[str] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(String(32))  # pluviometro | meteorologica | estacao_ar | ...
    geom: Mapped[object] = mapped_column(Geometry("POINT", srid=4326))
    bairro_id: Mapped[int | None] = mapped_column(ForeignKey("bairro.id"))
    ra_id: Mapped[int | None] = mapped_column(ForeignKey("ra.id"))
    h3_r8: Mapped[str | None] = mapped_column(String(16))
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (UniqueConstraint("fonte_id", "codigo_externo"),)
