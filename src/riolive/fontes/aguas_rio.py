"""Comunicados da Águas do Rio (REST padrão do WordPress, categoria 449).

Baixa frequência, contexto (manutenção programada, interrupção de abastecimento).
A concessionária atende a região metropolitana inteira — comunicado pode ser de
fora do município; sem geo estruturada, tudo entra rotulado (curadoria na UI).
"""

import html
import json
import re
from datetime import datetime, timedelta

from riolive.fontes.comum import local_para_utc
from riolive.ingestao.contrato import ErroSchema, EventoNovo, FonteConfig, ResultadoColeta
from riolive.ingestao.fetcher import ClienteHttp

URL = "https://aguasdorio.com.br/wp-json/wp/v2/posts"
CATEGORIA_COMUNICADOS = "449"


def _texto_limpo(html_bruto: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", html_bruto)).strip()


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    resposta = cliente.obter(URL, params={"categories": CATEGORIA_COMUNICADOS, "per_page": "10"})
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} nos comunicados")
    try:
        posts = resposta.json()
    except json.JSONDecodeError as exc:
        raise ErroSchema(f"resposta não é JSON: {exc}") from exc
    if not isinstance(posts, list) or not posts:
        raise ErroSchema("WP sem lista de posts")

    eventos: list[EventoNovo] = []
    marca_frescor = None
    for post in posts:
        # `date` do WP vem no fuso do site (Rio), ingênuo
        inicio = local_para_utc(datetime.fromisoformat(post["date"]))
        marca_frescor = max(marca_frescor, inicio) if marca_frescor else inicio
        titulo = _texto_limpo(post.get("title", {}).get("rendered", "")) or "Comunicado"
        eventos.append(
            EventoNovo(
                tipo="agua",
                severidade=2,
                inicio=inicio,
                fim=inicio,  # comunicado é pontual; a vigência real fica no texto
                titulo=f"Águas do Rio: {titulo}"[:200],
                descricao=_texto_limpo(post.get("excerpt", {}).get("rendered", ""))[:500] or None,
                payload={"link": post.get("link")},
            )
        )
    return ResultadoColeta(eventos=eventos, marca_frescor=marca_frescor)


FONTE = FonteConfig(
    slug="aguas_rio",
    nome="Comunicados de abastecimento (Águas do Rio)",
    orgao="Águas do Rio",
    url=URL,
    bloco="D",
    criticidade=2,
    cadencia=timedelta(hours=1),
    tolerancia_frescor=timedelta(days=30),  # semanas sem comunicado é normal
    coletar=coletar,
)
