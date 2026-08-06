"""GET /fontes — status público de todas as fontes (a página da transparência)."""

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from riolive.db import sessao

rota = APIRouter(tags=["fontes"])


@rota.get("/fontes")
def listar_fontes() -> list[dict[str, Any]]:
    with sessao() as s:
        linhas = s.execute(
            text(
                """
                SELECT f.slug, f.nome, f.orgao, f.bloco, f.criticidade,
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
        }
        for linha in linhas
    ]
