"""Planejado × realizado (Tese 3): GTFS vigente agora × GPS da frota.

`linhas_agora()` é a consulta central: pra cada linha com frequência PLANEJADA
neste instante (calendário do dia + janela de frequência), quantos veículos
distintos rodaram nos últimos 15 min e quando foi a última posição.

O detector de linha parada (o ativo original do projeto) é `detectar_paradas()`:
linha planejada agora, sem nenhum veículo há 40+ min, mas que já circulou dentro
da janela de frequência vigente (distingue "parou" de "ainda não começou"). Ele
NUNCA roda com o GPS fora do ar — fonte quebrada geraria um falso positivo em
massa; a máquina de saúde é a trava.
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
-- O GTFS conta o dia de serviço a partir das 00:00 e admite hora acima de 24 h:
-- a linha que roda das 23h às 25h pertence ao dia ANTERIOR. Comparar só o
-- relógio (0-86399) fazia 1.041 janelas sumirem do planejado na madrugada, e
-- outras 430 (que começam depois da meia-noite) nunca casarem com nada.
dias AS (
  SELECT d AS dia, dow, seg FROM agora_rio
  UNION ALL
  SELECT d - 1, (dow + 6) % 7, seg + 86400 FROM agora_rio
),
servicos AS (
  SELECT h.dia, h.seg, c.service_id FROM gtfs_calendar c
  JOIN dias h ON c.inicio <= h.dia AND c.fim >= h.dia AND ((c.dias >> h.dow) & 1) = 1
  UNION
  SELECT h.dia, h.seg, cd.service_id FROM gtfs_calendar_dates cd
  JOIN dias h ON cd.data = h.dia AND cd.exception_type = 1
  EXCEPT
  SELECT h.dia, h.seg, cd.service_id FROM gtfs_calendar_dates cd
  JOIN dias h ON cd.data = h.dia AND cd.exception_type = 2
),
planejadas AS (
  SELECT r.short_name AS linha, r.long_name AS nome, min(f.headway_seg) AS headway_seg,
         max(s.dia) AS dia_servico
  FROM gtfs_frequencies f
  JOIN gtfs_trips t ON t.trip_id = f.trip_id
  JOIN gtfs_routes r ON r.route_id = t.route_id
  JOIN servicos s ON s.service_id = t.service_id
  WHERE f.inicio_seg <= s.seg AND f.fim_seg > s.seg AND r.short_name <> ''
  GROUP BY r.short_name, r.long_name
),
-- Início da operação do dia DA LINHA: a primeira janela de frequência dela no
-- dia de serviço. É o marco de "já circulou hoje" — a metade das janelas do GTFS
-- dura 1 h, então ancorar na janela vigente zeraria o relógio de hora em hora e
-- cegaria o detector.
inicio_operacao AS (
  SELECT r.short_name AS linha, s.dia,
         min((s.dia + make_interval(secs => f.inicio_seg))
             AT TIME ZONE 'America/Sao_Paulo') AS inicio
  FROM gtfs_frequencies f
  JOIN gtfs_trips t ON t.trip_id = f.trip_id
  JOIN gtfs_routes r ON r.route_id = t.route_id
  JOIN servicos s ON s.service_id = t.service_id
  WHERE r.short_name <> ''
  GROUP BY r.short_name, s.dia
),
realizadas AS (
  SELECT linha, count(DISTINCT veiculo_id) AS veiculos
  FROM posicao
  WHERE modal IN ('onibus', 'brt') AND ts > now() - interval '15 minutes'
  GROUP BY linha
),
-- Duas leituras da mesma pergunta, cada uma na fonte barata pra ela:
-- `ultima` é precisa mas só olha 6 h (scan curto na hypertable); `ultimo_bucket`
-- vem do agregado de 15 min e alcança o dia inteiro sem varrer posição bruta.
-- O recorte por linha vira condição do join adiante — varrer por linha, com um
-- marco diferente pra cada, faz a consulta passar de meio segundo pra quinze.
ultimas AS (
  SELECT linha, max(ts) AS ultima
  FROM posicao
  WHERE modal IN ('onibus', 'brt') AND ts > now() - interval '6 hours'
  GROUP BY linha
),
circulou AS (
  SELECT linha, max(bucket) AS ultimo_bucket
  FROM frota_veiculo_15min
  WHERE modal IN ('onibus', 'brt')
    AND bucket >= (SELECT min(inicio) FROM inicio_operacao)
    AND bucket > now() - interval '30 hours'  -- trava de varredura
  GROUP BY linha
)
SELECT p.linha, p.nome, p.headway_seg,
       coalesce(re.veiculos, 0) AS veiculos,
       u.ultima,
       c.ultimo_bucket
FROM planejadas p
JOIN inicio_operacao io ON io.linha = p.linha AND io.dia = p.dia_servico
LEFT JOIN realizadas re ON re.linha = p.linha
LEFT JOIN circulou c ON c.linha = p.linha AND c.ultimo_bucket >= io.inicio
LEFT JOIN ultimas u ON u.linha = p.linha AND u.ultima >= io.inicio
ORDER BY coalesce(re.veiculos, 0), p.headway_seg
"""


@dataclass
class LinhaAgora:
    linha: str
    nome: str
    headway_seg: int
    veiculos: int
    # None = nenhuma posição desde o início da janela planejada vigente: a linha
    # não parou, ela não iniciou a operação desta janela (ou não opera hoje)
    minutos_sem_gps: int | None


BUCKET_AGREGADO_MIN = 15  # o agregado fecha em janelas de 15 min


def linhas_agora(sessao: Session) -> list[LinhaAgora]:
    saida = []
    for r in sessao.execute(text(SQL_LINHAS)).all():
        # Silêncio de até 6 h sai preciso da hypertable; passando disso, o
        # agregado ainda sabe dizer quando a linha rodou pela última vez hoje.
        # Nenhum dos dois = não circulou desde o início da operação: não parou,
        # não começou.
        minutos = None
        marco = r.ultima
        if marco is None and r.ultimo_bucket is not None:
            marco = r.ultimo_bucket
        if marco is not None:
            idade = sessao.execute(
                text("SELECT EXTRACT(EPOCH FROM now() - :ts)::int / 60"), {"ts": marco}
            ).scalar_one()
            minutos = int(idade)
            if r.ultima is None:
                minutos -= BUCKET_AGREGADO_MIN  # o bucket é o INÍCIO da janela de 15 min
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


MIN_ONLINE_CONTINUO = 20  # minutos de fonte online contínua antes de confiar
FROTA_MINIMA_ONIBUS = 1500  # abaixo disso a janela de 15 min ainda está repovoando


def gps_confiavel(sessao: Session) -> tuple[bool, str]:
    """Trava do detector contra falso positivo em massa.

    Três condições (aprendidas com a rajada de 111 falsos no flapping do SPPO em
    2026-08-06): fonte online, online há 20+ min CONTÍNUOS (a transição recente
    significa janela ainda repovoando), e frota mínima de ônibus transmitindo.
    """
    linha = sessao.execute(
        text(
            "SELECT DISTINCT ON (f.slug) u.estado, "
            "EXTRACT(EPOCH FROM now() - u.ts)::int / 60 AS minutos "
            "FROM saude_fonte u JOIN fonte f ON f.id = u.fonte_id "
            "WHERE f.slug = 'gps_sppo' ORDER BY f.slug, u.ts DESC"
        )
    ).first()
    if linha is None or linha.estado != "online":
        return False, "GPS da frota fora do ar"
    if linha.minutos < MIN_ONLINE_CONTINUO:
        return False, f"GPS voltou há {linha.minutos} min — aguardando janela repovoar"
    frota = sessao.execute(
        text(
            "SELECT count(DISTINCT veiculo_id) FROM posicao "
            "WHERE modal = 'onibus' AND ts > now() - interval '15 minutes'"
        )
    ).scalar_one()
    if frota < FROTA_MINIMA_ONIBUS:
        return False, f"só {frota} ônibus transmitindo — janela incompleta"
    return True, "ok"


def gps_saudavel(sessao: Session) -> bool:
    return gps_confiavel(sessao)[0]


def detectar_paradas(linhas: list[LinhaAgora]) -> list[LinhaAgora]:
    """Planejada agora, já circulou nesta janela, e sem NENHUM veículo há 40+ min."""
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
