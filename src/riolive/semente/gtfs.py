"""Seed do GTFS estático da SMTR (o "planejado" da Tese 3).

Baixa o zip mensal do ArcGIS (CC-BY 4.0), trunca as tabelas gtfs_* e recarrega
tudo via COPY (stop_times tem ~2 mi de linhas). Re-executável a cada release
mensal do feed: `python -m riolive.semente.gtfs [caminho/do/gtfs.zip]`.

Horários GTFS passam de meia-noite ("25:30:00" = 01:30 do dia seguinte):
convertidos pra segundos desde a meia-noite do dia de serviço.
"""

import csv
import io
import logging
import sys
import tempfile
import zipfile
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from riolive.db import sessao
from riolive.ingestao.fetcher import ClienteHttp

logger = logging.getLogger(__name__)

ITEM_ARCGIS = "8ffe62ad3b2f42e49814bf941654ea6c"
URL_ZIP = f"https://www.arcgis.com/sharing/rest/content/items/{ITEM_ARCGIS}/data"


def _seg(hora: str) -> str:
    """'25:30:00' → segundos desde meia-noite ('' → NULL do COPY)."""
    if not hora:
        return ""
    h, m, s = hora.split(":")
    return str(int(h) * 3600 + int(m) * 60 + int(s))


def _bitmask_dias(linha: dict[str, str]) -> str:
    dias = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    return str(sum(1 << i for i, dia in enumerate(dias) if linha.get(dia) == "1"))


def _data_iso(bruta: str) -> str:
    return f"{bruta[:4]}-{bruta[4:6]}-{bruta[6:8]}" if bruta else ""


# tabela → (arquivo do zip, colunas destino, transformação linha-do-csv → tupla)
CARGAS: list[tuple[str, str, list[str], Callable[[dict[str, str]], tuple[str, ...]]]] = [
    (
        "gtfs_routes",
        "routes.txt",
        ["route_id", "agency_id", "short_name", "long_name", "route_type"],
        lambda r: (
            r["route_id"],
            r.get("agency_id", ""),
            r.get("route_short_name", ""),
            r.get("route_long_name", ""),
            r.get("route_type", ""),
        ),
    ),
    (
        "gtfs_trips",
        "trips.txt",
        ["trip_id", "route_id", "service_id", "headsign", "direction_id", "shape_id"],
        lambda r: (
            r["trip_id"],
            r["route_id"],
            r["service_id"],
            r.get("trip_headsign", ""),
            r.get("direction_id", ""),
            r.get("shape_id", ""),
        ),
    ),
    (
        "gtfs_stops",
        "stops.txt",
        ["stop_id", "nome", "lat", "lon"],
        lambda r: (
            r["stop_id"],
            r.get("stop_name", ""),
            r.get("stop_lat", ""),
            r.get("stop_lon", ""),
        ),
    ),
    (
        "gtfs_shapes",
        "shapes.txt",
        ["shape_id", "seq", "lat", "lon"],
        lambda r: (
            r["shape_id"],
            r["shape_pt_sequence"],
            r["shape_pt_lat"],
            r["shape_pt_lon"],
        ),
    ),
    (
        "gtfs_stop_times",
        "stop_times.txt",
        ["trip_id", "stop_sequence", "stop_id", "chegada_seg", "partida_seg"],
        lambda r: (
            r["trip_id"],
            r["stop_sequence"],
            r["stop_id"],
            _seg(r.get("arrival_time", "")),
            _seg(r.get("departure_time", "")),
        ),
    ),
    (
        "gtfs_frequencies",
        "frequencies.txt",
        ["trip_id", "inicio_seg", "fim_seg", "headway_seg", "exact_times"],
        lambda r: (
            r["trip_id"],
            _seg(r["start_time"]),
            _seg(r["end_time"]),
            r["headway_secs"],
            r.get("exact_times", ""),
        ),
    ),
    (
        "gtfs_calendar",
        "calendar.txt",
        ["service_id", "dias", "inicio", "fim"],
        lambda r: (
            r["service_id"],
            _bitmask_dias(r),
            _data_iso(r["start_date"]),
            _data_iso(r["end_date"]),
        ),
    ),
    (
        "gtfs_calendar_dates",
        "calendar_dates.txt",
        ["service_id", "data", "exception_type"],
        lambda r: (r["service_id"], _data_iso(r["date"]), r["exception_type"]),
    ),
]


def _copiar(
    sessao_db: Session, tabela: str, colunas: list[str], linhas: Iterable[tuple[str, ...]]
) -> int:
    conexao = sessao_db.connection().connection.driver_connection
    total = 0
    with conexao.cursor() as cursor:  # type: ignore[union-attr]
        with cursor.copy(f"COPY {tabela} ({', '.join(colunas)}) FROM STDIN (FORMAT csv)") as copia:
            buffer = io.StringIO()
            escritor = csv.writer(buffer)
            for linha in linhas:
                escritor.writerow(linha)
                total += 1
                if total % 100_000 == 0:
                    copia.write(buffer.getvalue())
                    buffer.seek(0)
                    buffer.truncate()
            copia.write(buffer.getvalue())
    return total


def carregar(sessao_db: Session, zip_path: Path) -> dict[str, int]:
    z = zipfile.ZipFile(zip_path)
    contagens: dict[str, int] = {}
    for tabela, _, _, _ in CARGAS:
        sessao_db.execute(text(f"TRUNCATE {tabela}"))
    for tabela, arquivo, colunas, transformar in CARGAS:
        with z.open(arquivo) as f:
            leitor = csv.DictReader(io.TextIOWrapper(f, "utf-8-sig"))
            contagens[tabela] = _copiar(
                sessao_db, tabela, colunas, (transformar(linha) for linha in leitor)
            )
        logger.info("%s: %s linhas", tabela, contagens[tabela])
    with z.open("feed_info.txt") as f:
        info = next(csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")), {})
    sessao_db.execute(
        text(
            "INSERT INTO gtfs_feed (carregado_em, feed_version, info) "
            "VALUES (:agora, :versao, cast(:info as jsonb))"
        ),
        {
            "agora": datetime.now(tz=UTC),
            "versao": info.get("feed_version"),
            "info": __import__("json").dumps(info),
        },
    )
    return contagens


def principal() -> None:
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1:
        zip_path = Path(sys.argv[1])
    else:
        zip_path = Path(tempfile.gettempdir()) / "riolive_gtfs.zip"
        logger.info("baixando o feed GTFS do ArcGIS…")
        with ClienteHttp() as cliente:
            resposta = cliente.obter(URL_ZIP)
            resposta.raise_for_status()
            zip_path.write_bytes(resposta.content)
    with sessao() as s:
        contagens = carregar(s, zip_path)
    logger.info("GTFS carregado: %s", contagens)


if __name__ == "__main__":
    principal()
