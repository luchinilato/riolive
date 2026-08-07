"""Comunicados do Centro de Operações e Resiliência (RSS do WordPress do cor.rio).

Cobre o que nenhuma outra fonte nossa cobre: **interdições** de túneis, elevados
e vias por evento, e o **texto** que explica o Estágio da cidade — o número vem
da `estagio_cor`, mas é aqui que se lê "balanço de ventos".

A classificação não precisa de heurística: o feed traz `<category>` própria
("Interdições", "Estágios", "Previsão do Tempo"...). Usamos a do publicador.

O post é texto redacional, não medição: vira evento rotulado como comunicado,
com link pro original, e nunca alimenta número de cartão.

> Pegadinha inversa à do `metro_rio`: dá 403 pro IP residencial e 200 do
> datacenter. Quem coleta é produção, mas o teste local engana.
"""

import html
import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from defusedxml import ElementTree

from riolive.fontes.comum import erro_de_status
from riolive.ingestao.contrato import ErroSchema, EventoNovo, FonteConfig, ResultadoColeta
from riolive.ingestao.fetcher import ClienteHttp

URL = "https://cor.rio/feed/"

# categoria publicada pelo COR → (tipo do nosso evento, severidade)
CATEGORIAS = {
    "Interdições": ("interdicao", 2),
    "Estágios": ("comunicado_cor", 2),
    "Prevenção e Operação": ("comunicado_cor", 2),
    "Previsão do Tempo": ("comunicado_cor", 1),
}
PADRAO = ("comunicado_cor", 1)


def _texto(bruto: str | None) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", bruto or "")).strip()


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    resposta = cliente.obter(URL)
    if resposta.status_code != 200:
        raise erro_de_status(resposta.status_code, "feed do COR")
    return interpretar(resposta.text)


def interpretar(xml: str) -> ResultadoColeta:
    try:
        raiz = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise ErroSchema(f"feed do COR não é XML: {exc}") from exc
    itens = raiz.findall(".//item")
    if not itens:
        raise ErroSchema("feed do COR sem nenhum <item>")

    eventos: list[EventoNovo] = []
    marca_frescor: datetime | None = None
    for item in itens:
        bruto = item.findtext("pubDate")
        if not bruto:
            raise ErroSchema("item do feed sem pubDate")
        # pubDate do WordPress vem com offset explícito — aqui o fuso é honesto
        publicado = parsedate_to_datetime(bruto)
        marca_frescor = max(marca_frescor, publicado) if marca_frescor else publicado

        categorias = [c.text for c in item.findall("category") if c.text]
        # a categoria mais específica ganha; "Destaques"/"Últimas Notícias" são vitrine
        tipo, severidade = PADRAO
        for c in categorias:
            if c in CATEGORIAS:
                tipo, severidade = CATEGORIAS[c]
                break

        titulo = _texto(item.findtext("title")) or "Comunicado do COR"
        eventos.append(
            EventoNovo(
                tipo=tipo,
                severidade=severidade,
                inicio=publicado,
                fim=publicado,  # comunicado é pontual; a vigência real está no texto
                titulo=titulo[:200],
                descricao=_texto(item.findtext("description"))[:500] or None,
                payload={
                    "link": item.findtext("link"),
                    "guid": item.findtext("guid"),
                    "categorias": categorias,
                },
            )
        )
    return ResultadoColeta(eventos=eventos, marca_frescor=marca_frescor)


FONTE = FonteConfig(
    slug="cor_feed",
    nome="Comunicados do COR (interdições, estágios, previsão)",
    orgao="Centro de Operações e Resiliência — Prefeitura do Rio",
    url=URL,
    bloco="A",
    criticidade=3,
    cadencia=timedelta(minutes=10),
    # dia inteiro sem publicação é normal em dia calmo
    tolerancia_frescor=timedelta(days=2),
    coletar=coletar,
)
