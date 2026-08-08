"""Recorte territorial por zona popular — o vocabulário de quem mora aqui.

Zona não é divisão oficial: a Prefeitura organiza por Área de Planejamento, e
"Zona Norte" é fala, não administração. O mapeamento das 33 RAs nas quatro zonas
mora na migration 0006, declarado com os pontos discutíveis explicados; aqui só
entra o vocabulário aceito na API.

`Enum` em vez de `str` de propósito: `?zona=zonanorte` vira **422 com a lista
dos valores válidos**, e não uma lista vazia que o painel desenharia como "não
há estação nesta zona". Filtro que erra calado é pior que filtro que recusa.

**Quem não tem RA some do recorte.** É o certo para um corte territorial — as
boias de mar ficam fora do município, e evento sem geometria (o estágio do COR
vale para a cidade inteira) não pertence a zona nenhuma. Quem consome precisa
saber que zona escolhida é uma pergunta sobre território, não sobre a cidade.
"""

from enum import StrEnum
from typing import Annotated

from fastapi import Query


class Zona(StrEnum):
    CENTRO = "centro"
    SUL = "sul"
    NORTE = "norte"
    OESTE = "oeste"


ZonaQuery = Annotated[
    Zona | None,
    Query(description="Recorte por zona popular. Sem o parâmetro, a cidade inteira."),
]

# Comparação contra `ra.zona`, que é NULL em local/evento sem RA resolvida. O
# `CAST` existe porque o Postgres precisa do tipo do parâmetro para decidir o
# plano quando ele vem nulo — sem isso, "could not determine data type".
FILTRO_SQL = "(CAST(:zona AS text) IS NULL OR r.zona = :zona)"


def valor(zona: Zona | None) -> str | None:
    """O que vai no bind: o texto da zona, ou NULL para "a cidade inteira"."""
    return zona.value if zona else None
