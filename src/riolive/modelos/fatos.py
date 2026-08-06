"""Fatos: hypertables Timescale (medicao, posicao, evento, snapshot_cidade, saude_fonte).

As três naturezas físicas do dado (medição, posição, evento) carregam o mesmo envelope
de contexto: fonte, ts_evento/coletado_em, geo enriquecida e payload bruto em jsonb.
Hypertable, compressão e retenção são definidas na migration (SQL do Timescale);
aqui fica o mapeamento ORM.
"""

import uuid
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from riolive.modelos.base import Base, ts_tz

# Vocabulário controlado de `metrica` (disciplina exigida dos parsers; trade-off aceito na DEC)
METRICAS = frozenset(
    {
        "chuva_5min",
        "chuva_10min",
        "chuva_15min",
        "chuva_1h",
        "chuva_4h",
        "chuva_24h",
        "chuva_96h",
        "chuva_mes",
        "nivel_rio_cm",
        "pm25",
        "pm10",
        "o3",
        "no2",
        "co",
        "so2",
        "vel_kmh",
        "vel_livre_kmh",
        "onda_altura_m",
        "temp_c",
        "sensacao_termica_c",
        "vento_kmh",
        "vento_direcao_graus",
        "pressao_hpa",
        "umidade_pct",
    }
)

MODAIS = ("onibus", "brt", "aviao", "navio")
ESTADOS_FONTE = ("online", "degradada", "fora", "congelada")
CLASSES_FALHA = ("rede", "schema", "frescor")


class Medicao(Base):
    """Série contínua de estação/ponto fixo. Pequena e eterna: é a Tese 2 (memória)."""

    __tablename__ = "medicao"

    ts: Mapped[ts_tz]
    local_id: Mapped[int] = mapped_column(ForeignKey("local.id"))
    fonte_id: Mapped[int] = mapped_column(ForeignKey("fonte.id"))
    metrica: Mapped[str] = mapped_column(String(32))
    valor: Mapped[float]
    coletado_em: Mapped[ts_tz]
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (PrimaryKeyConstraint("local_id", "metrica", "ts"),)


class Posicao(Base):
    """Telemetria móvel (~12 mi/dia). Bruto por 90 dias; agregados pra sempre."""

    __tablename__ = "posicao"

    ts: Mapped[ts_tz]
    modal: Mapped[str] = mapped_column(String(8))
    veiculo_id: Mapped[str] = mapped_column(String(32))
    linha: Mapped[str | None] = mapped_column(String(32))
    geom: Mapped[object] = mapped_column(Geometry("POINT", srid=4326))
    velocidade: Mapped[int | None] = mapped_column(SmallInteger)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    coletado_em: Mapped[ts_tz]

    __table_args__ = (
        # Janelas de coleta do SPPO se sobrepõem: ON CONFLICT DO NOTHING deduplica
        PrimaryKeyConstraint("modal", "veiculo_id", "ts"),
        CheckConstraint(f"modal IN {MODAIS!r}"),
    )


class Evento(Base):
    """Acontecimento com início, fim e severidade (estágio COR, sirene, tiroteio...)."""

    __tablename__ = "evento"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    tipo: Mapped[str] = mapped_column(String(32))
    fonte_id: Mapped[int] = mapped_column(ForeignKey("fonte.id"))
    # 1 a 5, espelhando os estágios do COR (1 = normalidade, 5 = crise)
    severidade: Mapped[int] = mapped_column(SmallInteger)
    inicio: Mapped[ts_tz]
    fim: Mapped[ts_tz | None] = mapped_column(nullable=True)  # NULL = vigente
    titulo: Mapped[str] = mapped_column(Text)
    descricao: Mapped[str | None] = mapped_column(Text)
    # Para tipos sensíveis (segurança), geom é NULL por contrato do parser: só h3_r8/bairro
    geom: Mapped[object | None] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    bairro_id: Mapped[int | None] = mapped_column(ForeignKey("bairro.id"))
    ra_id: Mapped[int | None] = mapped_column(ForeignKey("ra.id"))
    h3_r8: Mapped[str | None] = mapped_column(String(16))
    # Atraso deliberado da camada de segurança; a API pública lê só vw_evento_publico
    visivel_apos: Mapped[ts_tz | None] = mapped_column(nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    coletado_em: Mapped[ts_tz]

    __table_args__ = (
        # Hypertable particionada por `inicio`: a PK precisa incluir a coluna de partição
        PrimaryKeyConstraint("inicio", "id"),
        CheckConstraint("severidade BETWEEN 1 AND 5"),
    )


class SnapshotCidade(Base):
    """Fotografia da cidade a cada 15 min: replay da UI e estado_atual() da fase 3."""

    __tablename__ = "snapshot_cidade"

    ts: Mapped[ts_tz] = mapped_column(primary_key=True)
    ici: Mapped[float | None] = mapped_column(Numeric, nullable=True)  # índice adiado pra v2
    componentes: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    contadores: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class SaudeFonte(Base):
    """Transições da máquina de estados do monitoramento. Status page = último estado por fonte."""

    __tablename__ = "saude_fonte"

    ts: Mapped[ts_tz]
    fonte_id: Mapped[int] = mapped_column(ForeignKey("fonte.id"))
    estado: Mapped[str] = mapped_column(String(16))
    classe_falha: Mapped[str | None] = mapped_column(String(16), nullable=True)
    latencia_ms: Mapped[int | None] = mapped_column(Integer)
    detalhe: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("fonte_id", "ts"),
        CheckConstraint(f"estado IN {ESTADOS_FONTE!r}"),
        CheckConstraint(f"classe_falha IS NULL OR classe_falha IN {CLASSES_FALHA!r}"),
    )


class BlobManifesto(Base):
    """Manifesto de blobs guardados fora do banco (radar PNG, PDFs INEA)."""

    __tablename__ = "blob_manifesto"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    fonte_id: Mapped[int] = mapped_column(ForeignKey("fonte.id"))
    ts: Mapped[ts_tz]
    path: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
