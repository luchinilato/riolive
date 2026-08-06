"""GET /agora — o estado da cidade num payload só (alimenta o cabeçalho e o cockpit)."""

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["agora"])


@rota.get("/agora")
def agora() -> dict[str, Any]:
    with sessao() as s:
        snapshot = s.execute(
            text("SELECT ts, contadores FROM snapshot_cidade ORDER BY ts DESC LIMIT 1")
        ).first()
        estagio = s.execute(
            text(
                "SELECT severidade, titulo, inicio FROM evento "
                "WHERE tipo = 'estagio_cor' AND fim IS NULL ORDER BY inicio DESC LIMIT 1"
            )
        ).first()
        veiculos = s.execute(
            text(
                "SELECT modal, count(DISTINCT veiculo_id) FROM posicao "
                "WHERE ts > now() - interval '15 minutes' GROUP BY modal"
            )
        ).all()
    return {
        "estagio": (
            {"severidade": estagio[0], "titulo": estagio[1], "inicio": estagio[2].isoformat()}
            if estagio
            else None
        ),
        "veiculos_ativos": {modal: n for modal, n in veiculos},
        "snapshot": (
            {"ts": snapshot[0].isoformat(), "contadores": snapshot[1]} if snapshot else None
        ),
    }
