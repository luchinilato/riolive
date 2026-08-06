"""Contrato config-driven de fonte: cada fonte é um módulo que exporta uma FonteConfig.

A FonteConfig declara identidade (pra dimensão `fonte`), cadência, criticidade e a
função `coletar`, que busca, valida (Pydantic) e traduz o payload bruto pros
registros tipados do modelo. Erros são classificados nas classes de falha da
máquina de estados: rede (ErroRede, do fetcher) e schema (ErroSchema, daqui);
a classe frescor é derivada de `marca_frescor` pelo executor.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel

from riolive.ingestao.fetcher import ClienteHttp


class ErroSchema(Exception):
    """HTTP ok, mas o payload não bate com o schema esperado. Nunca se resolve sozinho."""


class LocalNovo(BaseModel):
    codigo_externo: str
    nome: str
    tipo: str
    lat: float
    lon: float
    extra: dict[str, Any] | None = None


class MedicaoNova(BaseModel):
    codigo_local: str  # codigo_externo do local na fonte
    metrica: str
    ts: datetime
    valor: float
    payload: dict[str, Any] | None = None


class PosicaoNova(BaseModel):
    modal: str
    veiculo_id: str
    ts: datetime
    lat: float
    lon: float
    linha: str | None = None
    velocidade: int | None = None
    extra: dict[str, Any] | None = None


class EventoNovo(BaseModel):
    tipo: str
    severidade: int  # 1 a 5, escala dos estágios do COR
    inicio: datetime
    titulo: str
    descricao: str | None = None
    fim: datetime | None = None
    lat: float | None = None  # NULL por contrato do parser em tipos sensíveis
    lon: float | None = None
    visivel_apos: datetime | None = None
    payload: dict[str, Any] | None = None
    # Tipos "vigentes" (ex. estágio da cidade): só existe um evento aberto por tipo;
    # mudança fecha o anterior e abre outro. Ver gravacao.gravar_eventos_vigentes.
    vigente: bool = False


@dataclass(frozen=True)
class ResultadoColeta:
    medicoes: list[MedicaoNova] = field(default_factory=list)
    posicoes: list[PosicaoNova] = field(default_factory=list)
    eventos: list[EventoNovo] = field(default_factory=list)
    locais: list[LocalNovo] = field(default_factory=list)
    # Timestamp mais recente do dado em si (não da coleta): insumo do detector de
    # congelamento. None = fonte sem noção de frescor própria.
    marca_frescor: datetime | None = None


@dataclass(frozen=True)
class FonteConfig:
    slug: str
    nome: str
    orgao: str
    url: str
    bloco: str  # A clima | B mobilidade | C segurança | D cidade | E histórico
    criticidade: int  # 1 a 5
    cadencia: timedelta  # de coleta (schedule do Dagster)
    tolerancia_frescor: timedelta  # dado mais velho que isso = fonte congelada
    coletar: Callable[[ClienteHttp], ResultadoColeta]
    licenca: str | None = None

    @property
    def quente(self) -> bool:
        """Fontes de cadência ≤ 1 min entram no job agregador."""
        return self.cadencia <= timedelta(minutes=1)
