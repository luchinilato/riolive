"""Utilidades compartilhadas pelos parsers de fonte."""

from datetime import datetime
from zoneinfo import ZoneInfo

from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ErroRede

TZ_RIO = ZoneInfo("America/Sao_Paulo")

# Caixa ampla da região metropolitana: descarta coordenada obviamente inválida (0,0 etc.)
LAT_MIN, LAT_MAX = -23.6, -22.2
LON_MIN, LON_MAX = -44.4, -42.4


def coordenada_plausivel(lat: float, lon: float) -> bool:
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX


def local_para_utc(momento_naive: datetime) -> datetime:
    """Timestamp ingênuo em hora do Rio → aware em UTC."""
    return momento_naive.replace(tzinfo=TZ_RIO).astimezone(ZoneInfo("UTC"))


# Status que significam "o servidor não quis me atender agora", não "o formato mudou".
# 403 entra aqui por causa do Cloudflare: em 2026-08-07 o cor.rio alternou entre
# 200 e 403 para o MESMO cliente em minutos, por reputação de IP — chamar isso de
# mudança de schema marca a fonte com a classe errada e alerta o time à toa.
STATUS_TRANSITORIOS = (403, 408, 425, 429)


def erro_de_status(status: int, contexto: str) -> Exception:
    """Escolhe a classe de falha a partir do status HTTP.

    Transitório vira `ErroRede` (a máquina de saúde trata como oscilação);
    o resto vira `ErroSchema`, que é o sinal de "a origem mudou e o parser
    precisa de atenção humana".
    """
    if status in STATUS_TRANSITORIOS:
        return ErroRede(f"HTTP {status} em {contexto}")
    return ErroSchema(f"HTTP {status} em {contexto}")
