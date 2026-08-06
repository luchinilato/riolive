"""Snapshot da cidade: a "fotografia" resumida gravada a cada 15 min.

Alimenta o replay da UI ("como estava a cidade ontem às 18h?") e o estado_atual()
da fase 3 — uma linha por instante, sem reprocessar milhões de posições.
ICI fica NULL (índice adiado pra v2); `contadores` carrega o resumo.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from riolive.db import sessao
from riolive.modelos import SnapshotCidade

CONSULTAS: dict[str, str] = {
    "estagio": """
        SELECT jsonb_build_object('severidade', severidade, 'titulo', titulo)
        FROM evento WHERE tipo = 'estagio_cor' AND fim IS NULL
        ORDER BY inicio DESC LIMIT 1
    """,
    "veiculos_ativos": """
        SELECT jsonb_object_agg(modal, n) FROM (
            SELECT modal, count(DISTINCT veiculo_id) n FROM posicao
            WHERE ts > now() - interval '15 minutes' GROUP BY modal
        ) x
    """,
    "chuva": """
        SELECT jsonb_build_object('max_15min', max(valor) FILTER (WHERE metrica = 'chuva_15min'),
                                  'max_1h', max(valor) FILTER (WHERE metrica = 'chuva_1h'))
        FROM medicao WHERE metrica IN ('chuva_15min', 'chuva_1h')
          AND ts > now() - interval '1 hour'
    """,
    "nivel_rios_max_cm": """
        SELECT to_jsonb(max(valor)) FROM medicao
        WHERE metrica = 'nivel_rio_cm' AND ts > now() - interval '1 hour'
    """,
    "pm25_max": """
        SELECT to_jsonb(max(valor)) FROM medicao
        WHERE metrica = 'pm25' AND ts > now() - interval '2 hours'
    """,
    "eventos_abertos": """
        SELECT jsonb_object_agg(tipo, n) FROM (
            SELECT tipo, count(*) n FROM evento WHERE fim IS NULL GROUP BY tipo
        ) x
    """,
    "fontes": """
        SELECT jsonb_object_agg(estado, n) FROM (
            SELECT estado, count(*) n FROM (
                SELECT DISTINCT ON (fonte_id) estado FROM saude_fonte
                ORDER BY fonte_id, ts DESC
            ) ultimo GROUP BY estado
        ) x
    """,
}


def montar_contadores(sessao_db: Session) -> dict[str, Any]:
    contadores: dict[str, Any] = {}
    for chave, sql in CONSULTAS.items():
        contadores[chave] = sessao_db.execute(text(sql)).scalar()
    return contadores


def gravar_snapshot() -> dict[str, Any]:
    with sessao() as s:
        contadores = montar_contadores(s)
        s.add(SnapshotCidade(ts=datetime.now(tz=UTC), ici=None, contadores=contadores))
    return contadores
