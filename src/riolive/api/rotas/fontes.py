"""GET /fontes — status público de todas as fontes (a página da transparência).

O uptime é reconstruído da máquina de estados (saude_fonte guarda transições):
pra cada dia dos últimos 30, o pior estado em vigor naquele dia; % de uptime =
fração do tempo OBSERVADO em `online` (honesto: antes da primeira coleta não há
dado, e isso aparece como "sem dado", não como 100%).
"""

from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["fontes"])

TZ_RIO = ZoneInfo("America/Sao_Paulo")
GRAVIDADE = {"online": 0, "degradada": 1, "congelada": 2, "fora": 3}
DIAS_BARRAS = 30


def _uptime_por_fonte(transicoes: Sequence[Any]) -> dict[int, dict[str, Any]]:
    """Reconstrói, por fonte: pior estado por dia (30 dias) e % do tempo em online."""
    por_fonte: dict[int, list[Any]] = defaultdict(list)
    for linha in transicoes:
        por_fonte[linha.fonte_id].append(linha)

    agora = datetime.now(tz=UTC)
    hoje_rio = agora.astimezone(TZ_RIO).date()
    saida: dict[int, dict[str, Any]] = {}
    for fonte_id, eventos in por_fonte.items():
        eventos.sort(key=lambda e: e.ts)
        # % de uptime sobre o tempo observado (da 1ª transição até agora)
        online_s = 0.0
        for atual, proximo in zip(eventos, [*eventos[1:], None], strict=False):
            fim = proximo.ts if proximo else agora
            if atual.estado == "online":
                online_s += (fim - atual.ts).total_seconds()
        observado_s = (agora - eventos[0].ts).total_seconds()
        uptime_pct = round(100 * online_s / observado_s, 1) if observado_s > 0 else None

        dias = []
        for atras in range(DIAS_BARRAS - 1, -1, -1):
            dia = hoje_rio - timedelta(days=atras)
            inicio_dia = datetime.combine(dia, datetime.min.time(), tzinfo=TZ_RIO)
            fim_dia = inicio_dia + timedelta(days=1)
            herdado = None
            pior = None
            for e in eventos:
                if e.ts < inicio_dia:
                    herdado = e.estado
                elif e.ts < fim_dia:
                    pior = (
                        e.estado
                        if pior is None
                        else max(pior, e.estado, key=lambda s: GRAVIDADE[s])
                    )
            candidatos = [s for s in (herdado, pior) if s is not None]
            dominante = max(candidatos, key=lambda s: GRAVIDADE[s]) if pior else (herdado or None)
            dias.append(dominante)
        saida[fonte_id] = {"uptime_pct": uptime_pct, "dias": dias}
    return saida


@rota.get("/fontes")
def listar_fontes() -> list[dict[str, Any]]:
    with sessao() as s:
        linhas = s.execute(
            text(
                """
                SELECT f.id, f.slug, f.nome, f.orgao, f.bloco, f.criticidade,
                       f.cadencia_segundos, u.estado, u.classe_falha, u.ts, u.detalhe
                FROM fonte f
                LEFT JOIN LATERAL (
                    SELECT estado, classe_falha, ts, detalhe FROM saude_fonte
                    WHERE fonte_id = f.id ORDER BY ts DESC LIMIT 1
                ) u ON TRUE
                ORDER BY f.bloco, f.slug
                """
            )
        ).all()
        transicoes = s.execute(
            text("SELECT fonte_id, ts, estado FROM saude_fonte ORDER BY fonte_id, ts")
        ).all()
    uptime = _uptime_por_fonte(transicoes)
    return [
        {
            "slug": linha.slug,
            "nome": linha.nome,
            "orgao": linha.orgao,
            "bloco": linha.bloco,
            "criticidade": linha.criticidade,
            "cadencia_segundos": linha.cadencia_segundos,
            "estado": linha.estado or "desconhecido",
            "classe_falha": linha.classe_falha,
            "desde": linha.ts.isoformat() if linha.ts else None,
            "detalhe": linha.detalhe,
            "uptime_pct": uptime.get(linha.id, {}).get("uptime_pct"),
            "dias": uptime.get(linha.id, {}).get("dias", [None] * DIAS_BARRAS),
        }
        for linha in linhas
    ]
