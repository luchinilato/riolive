"""Seed das dimensões bairro e RA a partir do data.rio (camada oficial de limites).

Carga única (re-executável: upsert), rodada por `python -m riolive.semente.bairros`.
Depois da carga, re-enriquece `local` e `evento` que ficaram sem bairro por terem
sido gravados antes do seed. População por bairro fica NULL por ora (Censo 2022
por setor censitário é base separada — pendência conhecida do catálogo).
"""

import logging
from typing import Any

from shapely.geometry import MultiPolygon, shape
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from riolive.db import sessao
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp
from riolive.modelos import RA, Bairro

logger = logging.getLogger(__name__)

URL_BAIRROS = (
    "https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Cartografia/"
    "Limites_administrativos/FeatureServer/4/query"
)


def interpretar_feature(feature: dict[str, Any]) -> dict[str, Any]:
    """Feature do ArcGIS → linha da dimensão bairro (+ dados da RA)."""
    props = feature["properties"]
    geometria = shape(feature["geometry"])
    if geometria.geom_type == "Polygon":
        geometria = MultiPolygon([geometria])
    if geometria.geom_type != "MultiPolygon":
        raise ErroSchema(f"geometria inesperada em {props.get('nome')}: {geometria.geom_type}")
    return {
        "id": int(props["codbairro"]),
        "nome": str(props["nome"]).strip(),
        "ra_id": int(props["codra"]),
        "ra_nome": str(props["regiao_adm"]).strip(),
        "wkt": geometria.wkt,
    }


def carregar_bairros(sessao_db: Session, cliente: ClienteHttp) -> int:
    resposta = cliente.obter(URL_BAIRROS, params={"where": "1=1", "outFields": "*", "f": "geojson"})
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} na camada de bairros")
    corpo = resposta.json()
    features = corpo.get("features") or []
    if len(features) < 150:  # a cidade tem ~160 bairros; menos que isso é resposta quebrada
        raise ErroSchema(f"esperava ~160 bairros, vieram {len(features)}")

    linhas = [interpretar_feature(f) for f in features]

    ras = {linha["ra_id"]: linha["ra_nome"] for linha in linhas}
    for ra_id, nome in sorted(ras.items()):
        sessao_db.execute(
            insert(RA)
            .values(id=ra_id, nome=nome)
            .on_conflict_do_update(index_elements=["id"], set_={"nome": nome})
        )
    for linha in linhas:
        sessao_db.execute(
            insert(Bairro)
            .values(
                id=linha["id"],
                nome=linha["nome"],
                ra_id=linha["ra_id"],
                geom=text("ST_GeomFromText(:wkt, 4326)").bindparams(wkt=linha["wkt"]),
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "nome": linha["nome"],
                    "ra_id": linha["ra_id"],
                    "geom": text("ST_GeomFromText(:wkt, 4326)").bindparams(wkt=linha["wkt"]),
                },
            )
        )
    return len(linhas)


def reenriquecer(sessao_db: Session) -> tuple[int, int]:
    """Preenche bairro/RA de locais e eventos gravados antes do seed."""
    locais = sessao_db.execute(
        text(
            "UPDATE local l SET bairro_id = b.id, ra_id = b.ra_id "
            "FROM bairro b WHERE l.bairro_id IS NULL AND ST_Contains(b.geom, l.geom)"
        )
    ).rowcount  # type: ignore[attr-defined]
    eventos = sessao_db.execute(
        text(
            "UPDATE evento e SET bairro_id = b.id, ra_id = b.ra_id "
            "FROM bairro b WHERE e.bairro_id IS NULL AND e.geom IS NOT NULL "
            "AND ST_Contains(b.geom, e.geom)"
        )
    ).rowcount  # type: ignore[attr-defined]
    return locais or 0, eventos or 0


def principal() -> None:
    logging.basicConfig(level=logging.INFO)
    with ClienteHttp() as cliente, sessao() as s:
        n_bairros = carregar_bairros(s, cliente)
        locais, eventos = reenriquecer(s)
    logger.info(
        "%s bairros carregados; re-enriquecidos %s locais e %s eventos",
        n_bairros,
        locais,
        eventos,
    )


if __name__ == "__main__":
    principal()
