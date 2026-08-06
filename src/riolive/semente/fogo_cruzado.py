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
PAUSA_S = 0.25  # gentileza com a API deles


def principal() -> None:
    logging.basicConfig(level=logging.INFO)
    total = 0
    pagina = 1
    with ClienteHttp() as cliente:
        token = _logar(cliente)
        while True:
            if pagina % PAGINAS_POR_LOGIN == 0:
                token = _logar(cliente)
            corpo = buscar_pagina(cliente, token, pagina, INICIO_HISTORIA)
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
