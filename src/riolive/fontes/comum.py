"""Utilidades compartilhadas pelos parsers de fonte."""

from datetime import datetime
from zoneinfo import ZoneInfo

TZ_RIO = ZoneInfo("America/Sao_Paulo")

# Caixa ampla da região metropolitana: descarta coordenada obviamente inválida (0,0 etc.)
LAT_MIN, LAT_MAX = -23.6, -22.2
LON_MIN, LON_MAX = -44.4, -42.4


def coordenada_plausivel(lat: float, lon: float) -> bool:
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX


def local_para_utc(momento_naive: datetime) -> datetime:
    """Timestamp ingênuo em hora do Rio → aware em UTC."""
    return momento_naive.replace(tzinfo=TZ_RIO).astimezone(ZoneInfo("UTC"))
