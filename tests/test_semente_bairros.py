"""Interpretação das features de bairro do data.rio (amostra real de 2026-08-06)."""

import json
from pathlib import Path

from riolive.semente.bairros import interpretar_feature


def _features(fixtures: Path) -> list[dict]:  # type: ignore[type-arg]
    corpo = json.loads((fixtures / "bairros_amostra.geojson").read_text())
    return list(corpo["features"])


def test_codigos_e_nomes_normalizados(fixtures: Path) -> None:
    grumari = next(
        interpretar_feature(f) for f in _features(fixtures) if f["properties"]["nome"] == "Grumari"
    )
    assert grumari["id"] == 133  # codbairro vem como string "133"
    assert grumari["ra_id"] == 24
    assert grumari["ra_nome"] == "BARRA DA TIJUCA"  # sem o padding de espaços da fonte
    assert grumari["wkt"].startswith("MULTIPOLYGON")


def test_polygon_vira_multipolygon(fixtures: Path) -> None:
    # A camada mistura Polygon e MultiPolygon; a coluna é MULTIPOLYGON
    sulacap = next(
        interpretar_feature(f)
        for f in _features(fixtures)
        if f["properties"]["nome"] == "Jardim Sulacap"
    )
    assert sulacap["wkt"].startswith("MULTIPOLYGON")
