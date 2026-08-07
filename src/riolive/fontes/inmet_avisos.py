"""Avisos meteorológicos do INMET (RSS no padrão CAP).

O que a fonte responde e nenhuma outra nossa responde: **o que vem por aí**, com
grau de perigo declarado pelo órgão federal. Na captura de 2026-08-07 o feed
trazia "Vendaval · Perigo · 13:45" para a área Metropolitana — e o COR declarou
Estágio 3 às 13h02 citando ventos. Uma fonte diz o que vem, a outra diz o que a
cidade decidiu fazer.

> [!warning] O aviso é REGIONAL
> O feed NÃO traz código IBGE nem geocode (conferido na fixture de 99 avisos): a
> área é macrorregião. O município do Rio entra dentro de "Metropolitana do Rio
> de Janeiro", e é assim que filtramos — então o evento é rotulado como aviso
> para a região, nunca para a cidade. Prometer recorte municipal aqui seria
> afirmar precisão que a fonte não tem.

Fuso: os horários vêm ingênuos e são **hora de Brasília** — as janelas de dia
inteiro fecham em 00:00–23:59 e as de baixa umidade em 10h–22h, que só fazem
sentido em hora local (a lição do `Z` mentiroso do SPPO vale pra toda fonte com
timestamp: desconfiar antes de confiar no rótulo).

O endpoint dá `connection reset` com frequência — inclusive pros nossos dois
IPs por horas seguidas. É falha transitória de rede, e a máquina de saúde vai
mostrar a fonte oscilando: é o comportamento correto do produto.
"""

import html
import re
import unicodedata
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from defusedxml import ElementTree

from riolive.fontes.comum import local_para_utc
from riolive.ingestao.contrato import ErroSchema, EventoNovo, FonteConfig, ResultadoColeta
from riolive.ingestao.fetcher import ClienteHttp

URL = "https://apiprevmet3.inmet.gov.br/avisos/rss"

# O município fica dentro desta macrorregião do INMET
AREA_DO_RIO = "metropolitana do rio de janeiro"

# grau declarado pelo INMET → severidade na escala do painel (1 a 5)
SEVERIDADE = {
    "perigo potencial": 2,
    "perigo": 3,
    "grande perigo": 4,
}


def _sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def _campo(descricao: str, nome: str) -> str:
    """A `description` do item é uma tabela HTML: <th>Campo</th><td>valor</td>."""
    achado = re.search(rf"<th[^>]*>{nome}</th><td>(.*?)</td>", descricao, re.S)
    if not achado:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", " ", achado.group(1))).strip()


def _instante(bruto: str) -> datetime | None:
    # "2026-08-07 13:45:00.0" — ingênuo, hora de Brasília
    try:
        ingenuo = datetime.strptime(bruto.strip(), "%Y-%m-%d %H:%M:%S.%f")  # noqa: DTZ007
        return local_para_utc(ingenuo)  # o fuso entra aqui: Brasília, não UTC
    except ValueError:
        return None


def _tipo(evento: str) -> str:
    """Um tipo por fenômeno.

    A dedup de evento pontual é (tipo, início, h3) e aqui não há geo: com um tipo
    único, três avisos distintos que começam à meia-noite colapsariam em um só.
    """
    limpo = re.sub(r"[^a-z0-9]+", "_", _sem_acento(evento).lower()).strip("_")
    return f"aviso_{limpo or 'meteorologico'}"


def _unir_reemissoes(eventos: list[EventoNovo]) -> list[EventoNovo]:
    """O INMET reemite o mesmo aviso com validade estendida — na captura de
    2026-08-07, dois de Tempestade e dois de Vendaval com o mesmo início e fins
    diferentes (02:53 e 02:59). Pro leitor é um alerta só, e a chave natural do
    banco (tipo, início) guardaria um e descartaria o outro em silêncio.

    Aqui a união é explícita: fica o grau mais alto e a validade mais longa, e o
    payload registra quantos avisos foram unidos.
    """
    por_chave: dict[tuple[str, datetime], EventoNovo] = {}
    for novo in eventos:
        chave = (novo.tipo, novo.inicio)
        atual = por_chave.get(chave)
        if atual is None:
            novo.payload = {**(novo.payload or {}), "avisos_unidos": 1}
            por_chave[chave] = novo
            continue
        unidos = (atual.payload or {}).get("avisos_unidos", 1) + 1
        vencedor = novo if novo.severidade > atual.severidade else atual
        vencedor.fim = max(
            (m for m in (atual.fim, novo.fim) if m is not None),
            default=None,
        )
        vencedor.payload = {**(vencedor.payload or {}), "avisos_unidos": unidos}
        por_chave[chave] = vencedor
    return list(por_chave.values())


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    resposta = cliente.obter(URL)
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} nos avisos do INMET")
    return interpretar(resposta.text)


def interpretar(xml: str) -> ResultadoColeta:
    try:
        raiz = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise ErroSchema(f"avisos do INMET não são XML: {exc}") from exc
    itens = raiz.findall(".//item")
    if not itens:
        raise ErroSchema("feed de avisos sem nenhum <item>")

    eventos: list[EventoNovo] = []
    reconhecidos = 0
    for item in itens:
        descricao = item.findtext("description") or ""
        evento = _campo(descricao, "Evento")
        area = _campo(descricao, "Área")
        if not evento or not area:
            continue  # item fora do formato de aviso; o guard de schema é o total
        reconhecidos += 1
        if AREA_DO_RIO not in _sem_acento(area).lower():
            continue

        grau = _campo(descricao, "Severidade")
        severidade = SEVERIDADE.get(_sem_acento(grau).lower())
        if severidade is None:
            raise ErroSchema(f"grau de severidade desconhecido no INMET: {grau!r}")
        inicio = _instante(_campo(descricao, "Início"))
        if inicio is None:
            raise ErroSchema("aviso do INMET sem início interpretável")

        eventos.append(
            EventoNovo(
                tipo=_tipo(evento),
                severidade=severidade,
                inicio=inicio,
                fim=_instante(_campo(descricao, "Fim")),
                titulo=f"{evento} — aviso {grau.lower()} para a região metropolitana"[:200],
                descricao=_campo(descricao, "Descrição")[:500] or None,
                payload={
                    "grau": grau,
                    "area": area,
                    "status": _campo(descricao, "Status"),
                    "link": item.findtext("link"),
                },
            )
        )

    if not reconhecidos:
        raise ErroSchema("nenhum item do feed tinha os campos Evento/Área — formato mudou")
    eventos = _unir_reemissoes(eventos)
    # Nenhum aviso pro Rio é o estado normal do país em dia calmo: não é falha.
    # O frescor é do feed, não dos avisos — por isso a marca sai do canal.
    publicado = raiz.findtext(".//channel/pubDate")
    marca = parsedate_to_datetime(publicado) if publicado else None
    return ResultadoColeta(eventos=eventos, marca_frescor=marca)


FONTE = FonteConfig(
    slug="inmet_avisos",
    nome="Avisos meteorológicos (INMET)",
    orgao="INMET — Instituto Nacional de Meteorologia",
    url=URL,
    bloco="A",
    criticidade=3,
    cadencia=timedelta(minutes=15),
    # o feed é nacional e sempre tem aviso em algum canto: frescor curto pega o
    # endpoint parando de responder, que é a falha real desta fonte
    tolerancia_frescor=timedelta(hours=6),
    coletar=coletar,
    licenca="domínio público",
)
