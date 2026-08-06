"""Dead-man's switch: ping periódico pro healthchecks.io.

Se o nosso worker morrer, o ping para e o serviço externo alerta — cobre o caso
em que o silêncio pareceria saúde. Chamado ao fim de cada rodada do job agregador.
"""

import logging

import httpx

from riolive.config import config

logger = logging.getLogger(__name__)


def pingar() -> None:
    url = config().healthchecks_url
    if not url:
        return
    try:
        httpx.get(url, timeout=10)
    except httpx.HTTPError as exc:
        # Falha no ping nunca derruba a ingestão; o próprio serviço alerta a ausência
        logger.warning("Ping do healthchecks falhou: %s", exc)
