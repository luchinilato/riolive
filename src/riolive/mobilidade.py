"""Planejado × realizado (Tese 3): GTFS vigente agora × GPS da frota.

`linhas_agora()` é a consulta central: pra cada linha com frequência PLANEJADA
neste instante (calendário do dia + janela de frequência), quantos veículos
distintos rodaram nos últimos 15 min e quando foi a última posição.

O detector de linha parada (o ativo original do projeto) é `detectar_paradas()`:
linha planejada agora, sem nenhum veículo há 40+ min, mas que já rodou hoje
(distingue "parou" de "não opera hoje"). Ele NUNCA roda com o GPS fora do ar —
fonte quebrada geraria um falso positivo em massa; a máquina de saúde é a trava.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

MIN_SEM_GPS_PARADA = 40  # minutos sem posição pra declarar linha parada (do design)
HEADWAY_MAX_RELEVANTE = 1800  # só linhas com frequência planejada ≤ 30 min

SQL_LINHAS = """
WITH agora_rio AS (
  SELECT (now() AT TIME ZONE 'America/Sao_Paulo')::date AS d,
         EXTRACT(EPOCH FROM (now() AT TIME ZONE 'America/Sao_Paulo')::time)::int AS seg,
         EXTRACT(ISODOW FROM (now() AT TIME ZONE 'America/Sao_Paulo'))::int - 1 AS dow
),
servicos AS (
  SELECT c.service_id FROM gtfs_calendar c, agora_rio h
  WHERE c.inicio <= h.d AND c.fim >= h.d AND ((c.dias >> h.dow) & 1) = 1
  UNION
  SELECT cd.service_id FROM gtfs_calendar_dates cd, agora_rio h
  WHERE cd.data = h.d AND cd.exception_type = 1
  EXCEPT
  SELECT cd.service_id FROM gtfs_calendar_dates cd, agora_rio h
  WHERE cd.data = h.d AND cd.exception_type = 2
),
planejadas AS (
  SELECT r.short_name AS linha, r.long_name AS nome, min(f.headway_seg) AS headway_seg
  FROM gtfs_frequencies f
  JOIN gtfs_trips t ON t.trip_id = f.trip_id
  JOIN gtfs_routes r ON r.route_id = t.route_id
  JOIN servicos s ON s.service_id = t.service_id
  CROSS JOIN agora_rio h
  WHERE f.inicio_seg <= h.seg AND f.fim_seg > h.seg AND r.short_name <> ''
  GROUP BY r.short_name, r.long_name
),
realizadas AS (
  SELECT linha, count(DISTINCT veiculo_id) AS veiculos
  FROM posicao
  WHERE modal IN ('onibus', 'brt') AND ts > now() - interval '15 minutes'
  GROUP BY linha
),
ultimas AS (
  SELECT linha, max(ts) AS ultima
  FROM posicao
  WHERE modal IN ('onibus', 'brt') AND ts > now() - interval '6 hours'
  GROUP BY linha
)
SELECT p.linha, p.nome, p.headway_seg,
       coalesce(re.veiculos, 0) AS veiculos,
       u.ultima
FROM planejadas p
LEFT JOIN realizadas re ON re.linha = p.linha
LEFT JOIN ultimas u ON u.linha = p.linha
ORDER BY coalesce(re.veiculos, 0), p.headway_seg
"""


@dataclass
class LinhaAgora:
    linha: str
    nome: str
    headway_seg: int
    veiculos: int
    minutos_sem_gps: int | None  # None = nenhuma posição em 6 h (provável: não opera/sem GPS)


def linhas_agora(sessao: Session) -> list[LinhaAgora]:
    saida = []
    for r in sessao.execute(text(SQL_LINHAS)).all():
        minutos = None
        if r.ultima is not None:
            idade = sessao.execute(
                text("SELECT EXTRACT(EPOCH FROM now() - :ts)::int / 60"), {"ts": r.ultima}
            ).scalar_one()
            minutos = int(idade)
        saida.append(
            LinhaAgora(
                linha=r.linha,
                nome=r.nome or "",
                headway_seg=r.headway_seg,
                veiculos=r.veiculos,
                minutos_sem_gps=minutos,
            )
        )
    return saida


def gps_saudavel(sessao: Session) -> bool:
    """Trava do detector: só detecta parada com o GPS online (senão é falso positivo em massa)."""
    estado = sessao.execute(
        text(
            "SELECT DISTINCT ON (f.slug) u.estado FROM saude_fonte u "
            "JOIN fonte f ON f.id = u.fonte_id WHERE f.slug = 'gps_sppo' "
            "ORDER BY f.slug, u.ts DESC"
        )
    ).scalar_one_or_none()
    return estado == "online"


def detectar_paradas(linhas: list[LinhaAgora]) -> list[LinhaAgora]:
    """Linha planejada agora, que rodou hoje, mas está sem NENHUM veículo há 40+ min."""
    return [
        li
        for li in linhas
        if li.headway_seg <= HEADWAY_MAX_RELEVANTE
        and li.veiculos == 0
        and li.minutos_sem_gps is not None
        and li.minutos_sem_gps >= MIN_SEM_GPS_PARADA
    ]


def resumo(linhas: list[LinhaAgora]) -> dict[str, Any]:
    planejadas = len(linhas)
    ativas = sum(1 for li in linhas if li.veiculos > 0)
    return {
        "linhas_planejadas_agora": planejadas,
        "linhas_ativas": ativas,
        "pct_ativas": round(100 * ativas / planejadas) if planejadas else None,
    }
