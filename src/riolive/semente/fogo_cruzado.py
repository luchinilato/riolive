"""Backfill do Fogo Cruzado desde 2016 ([[DEC - Backfill histórico antes do lançamento]]).

Pagina TODA a história da capital (28,6 mil ocorrências em 2026-08-06) e grava
via o mesmo caminho da ingestão (dedup natural torna re-execução segura).
Re-loga a cada ~50 páginas (token expira em 3600 s).

Uso: `python -m riolive.semente.fogo_cruzado`
"""

import logging
import time
from datetime import UTC, datetime

from riolive.db import sessao
from riolive.fontes.fogo_cruzado import FONTE, _logar, buscar_pagina, interpretar_ocorrencia
from riolive.ingestao.fetcher import ClienteHttp
from riolive.ingestao.gravacao import garantir_fonte, gravar_eventos

logger = logging.getLogger(__name__)

INICIO_HISTORIA = "2016-01-01"
PAGINAS_POR_LOGIN = 50
PAUSA_S = 1.0  # o rate limit deles derrubou a 0.25s (429 na página ~52)
ESPERA_429_S = 90


def _data_retomada() -> str:
    """Retoma da fronteira do backfill, IGNORANDO os últimos 7 dias.

    A coleta em tempo real grava o presente — usar o max(inicio) cru pularia
    todo o miolo da história (aconteceu em 2026-08-06).
    """
    from sqlalchemy import text

    with sessao() as s:
        fronteira = s.execute(
            text(
                "SELECT max(inicio)::date FROM evento "
                "WHERE tipo = 'tiroteio' AND inicio < now() - interval '7 days'"
            )
        ).scalar_one_or_none()
    if fronteira is None:
        return INICIO_HISTORIA
    return fronteira.isoformat()


def principal() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    inicio = _data_retomada()
    logger.info("começando de %s", inicio)
    total = 0
    pagina = 1
    with ClienteHttp() as cliente:
        token = _logar(cliente)
        while True:
            if pagina % PAGINAS_POR_LOGIN == 0:
                token = _logar(cliente)
            try:
                corpo = buscar_pagina(cliente, token, pagina, inicio)
            except Exception as exc:
                if "429" in str(exc):
                    logger.warning("rate limit (429): esperando %ss", ESPERA_429_S)
                    time.sleep(ESPERA_429_S)
                    token = _logar(cliente)
                    continue
                raise
            eventos = [interpretar_ocorrencia(o) for o in corpo["data"]]
            with sessao() as s:
                fonte_id = garantir_fonte(s, FONTE)
                total += gravar_eventos(s, fonte_id, eventos, datetime.now(tz=UTC))
            meta = corpo["pageMeta"]
            if pagina % 10 == 0 or not meta.get("hasNextPage"):
                logger.info(
                    "página %s/%s · %s inseridos até aqui",
                    pagina,
                    meta.get("pageCount"),
                    total,
                )
            if not meta.get("hasNextPage"):
                break
            pagina += 1
            time.sleep(PAUSA_S)
    logger.info("backfill completo: %s ocorrências inseridas", total)


if __name__ == "__main__":
    principal()
