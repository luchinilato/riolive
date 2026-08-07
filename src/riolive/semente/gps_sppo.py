"""Backfill de posições do GPS SPPO.

A origem serve janelas passadas (confirmado em 2026-08-07 até 30 h atrás), então
buraco na série de ônibus é recuperável — o handoff de 2026-08-06 supunha que não
era, e a troca de schema da SMTR provou o contrário na marra.

Retoma da última posição de ônibus no banco e caminha até agora em fatias. A
gravação é a mesma da ingestão, e a PK natural (modal, veiculo_id, ts) deduplica,
então re-executar é seguro e barato: fatia já preenchida insere zero.

Uso: `python -m riolive.semente.gps_sppo [--horas N]`
  sem --horas, retoma da fronteira do banco (limitada a MAX_HORAS)
"""

import argparse
import logging
import math
import time
from datetime import datetime, timedelta

from sqlalchemy import text

from riolive.db import sessao
from riolive.fontes.comum import TZ_RIO
from riolive.fontes.gps_sppo import coletar_janela
from riolive.ingestao.fetcher import ClienteHttp
from riolive.ingestao.gravacao import agora_utc, inserir_posicoes

logger = logging.getLogger(__name__)

# 10 min ≈ 89 mil registros / 30 MB / 10 s por requisição (medido em 2026-08-07).
# Escala linear até 40 min, mas fatia menor perde menos se a requisição falhar.
FATIA = timedelta(minutes=10)
PAUSA_S = 1.0
MAX_HORAS = 30  # até onde a origem provou servir histórico
MARGEM = timedelta(minutes=2)  # não persegue o presente; a coleta ao vivo cobre


def _fronteira() -> datetime | None:
    """Última posição de ônibus no banco, em hora local do Rio."""
    with sessao() as s:
        ultimo: datetime | None = s.execute(
            text("SELECT max(ts) FROM posicao WHERE modal = 'onibus'")
        ).scalar_one_or_none()
    return ultimo.astimezone(TZ_RIO) if ultimo else None


def principal(horas: float | None = None) -> None:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    fim_total = datetime.now(tz=TZ_RIO) - MARGEM
    teto = fim_total - timedelta(hours=MAX_HORAS)
    if horas is not None:
        inicio = fim_total - timedelta(hours=horas)
    else:
        fronteira = _fronteira()
        if fronteira is None:
            logger.error("banco sem posição de ônibus: passe --horas explicitamente")
            return
        inicio = fronteira
    if inicio < teto:
        logger.warning("recuo pedido passa de %s h; começando de %s", MAX_HORAS, teto)
        inicio = teto
    if inicio >= fim_total:
        logger.info("série já está em dia (fronteira %s) — nada a fazer", inicio)
        return

    fatias = math.ceil((fim_total - inicio) / FATIA)
    logger.info("backfill de %s até %s · %s fatias", inicio, fim_total, fatias)
    total = 0
    for n in range(fatias):
        fatia_ini = inicio + n * FATIA
        fatia_fim = min(fatia_ini + FATIA, fim_total)
        if fatia_ini >= fatia_fim:
            break
        with ClienteHttp() as cliente:
            resultado = coletar_janela(cliente, fatia_ini, fatia_fim)
        with sessao() as s:
            inseridos = inserir_posicoes(s, resultado.posicoes, agora_utc())
        total += inseridos
        logger.info(
            "fatia %s/%s (%s) · %s posições, %s novas · %s no total",
            n + 1,
            fatias,
            fatia_ini.strftime("%d/%m %H:%M"),
            len(resultado.posicoes),
            inseridos,
            total,
        )
        time.sleep(PAUSA_S)
    logger.info("backfill completo: %s posições inseridas", total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--horas",
        type=float,
        default=None,
        help="recuar N horas a partir de agora, em vez de retomar da fronteira do banco",
    )
    principal(parser.parse_args().horas)
