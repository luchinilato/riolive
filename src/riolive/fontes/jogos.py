"""Agenda de jogos dos 4 grandes via TheSportsDB (key de teste pública, ~30 req/min).

Só jogos em estádios DA CIDADE (filtro por venue no cliente — endpoint por venue
é premium). Estádios conhecidos ganham coordenada real: o jogo vira evento com
pino no mapa e entra no esquema de trânsito do painel Cidade viva.
"""

from datetime import UTC, datetime, timedelta

from riolive.ingestao.contrato import ErroSchema, EventoNovo, FonteConfig, ResultadoColeta
from riolive.ingestao.fetcher import ClienteHttp

URL_BASE = "https://www.thesportsdb.com/api/v1/json/3/eventsnext.php"
TIMES = {"134287": "Flamengo", "134296": "Fluminense", "134285": "Botafogo", "134282": "Vasco"}
DURACAO_JOGO = timedelta(hours=2, minutes=30)

# venue (normalizado) → (lat, lon)
ESTADIOS_RIO = {
    "maracan": (-22.9121, -43.2302),
    "nilton santos": (-22.8930, -43.2925),
    "são januário": (-22.8908, -43.2287),
    "sao januario": (-22.8908, -43.2287),
}


def _estadio_no_rio(venue: str) -> tuple[float, float] | None:
    normalizado = venue.lower()
    for chave, coords in ESTADIOS_RIO.items():
        if chave in normalizado:
            return coords
    return None


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    eventos: list[EventoNovo] = []
    respostas_ok = 0
    for time_id, apelido in TIMES.items():
        resposta = cliente.obter(URL_BASE, params={"id": time_id})
        if resposta.status_code != 200:
            continue
        respostas_ok += 1
        for jogo in resposta.json().get("events") or []:
            venue = jogo.get("strVenue") or ""
            coords = _estadio_no_rio(venue)
            if coords is None:
                continue  # jogo fora da cidade
            bruto_ts = jogo.get("strTimestamp")
            if not bruto_ts:
                continue
            inicio = datetime.fromisoformat(bruto_ts).replace(tzinfo=UTC)
            eventos.append(
                EventoNovo(
                    tipo="jogo",
                    severidade=1,
                    inicio=inicio,
                    fim=inicio + DURACAO_JOGO,
                    titulo=jogo.get("strEvent") or f"Jogo do {apelido}",
                    descricao=f"{jogo.get('strLeague') or ''} · {venue}".strip(" ·"),
                    lat=coords[0],
                    lon=coords[1],
                    payload={"liga": jogo.get("strLeague"), "estadio": venue, "time_id": time_id},
                )
            )
    if respostas_ok == 0:
        raise ErroSchema("nenhuma resposta válida do TheSportsDB pros 4 times")
    return ResultadoColeta(eventos=eventos)


FONTE = FonteConfig(
    slug="jogos",
    nome="Agenda de jogos na cidade (TheSportsDB)",
    orgao="TheSportsDB",
    url=URL_BASE,
    bloco="D",
    criticidade=2,
    cadencia=timedelta(hours=6),
    tolerancia_frescor=timedelta(days=365),  # agenda parada é normal
    coletar=coletar,
)
