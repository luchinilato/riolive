"""Imagens do radar meteorológico do Sumaré (Alerta Rio).

Buffer circular de 20 PNGs (~6 KB cada, um quadro novo a cada ~2 min) cobrindo
a região metropolitana inteira (bounds fixos SW -24.4316,-45.3370 /
NE -21.4788,-41.1591 — ficam no meta de cada blob pro frontend georreferenciar).
Timestamp do quadro = Last-Modified. O quadro vai pro armazém de blobs com
manifesto no banco; releitura do mesmo instante é deduplicada pelo caminho.

Retenção: 1 ano (~1.6 GB) por DEC. Análise de pixels (intensidade, chuva se
aproximando) fica pra melhoria futura — decisão de 2026-08-06.
"""

from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from riolive.ingestao.contrato import BlobNovo, ErroSchema, FonteConfig, ResultadoColeta
from riolive.ingestao.fetcher import ClienteHttp

URL_BASE = "https://sistema-alerta-rio.com.br/upload/Mapa/semfundo/"
QUADROS = [f"radar{n:03d}.png" for n in range(1, 21)]
BOUNDS = {"sw": [-24.4316, -45.3370], "ne": [-21.4788, -41.1591]}


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    blobs: list[BlobNovo] = []
    marca_frescor: datetime | None = None
    falhas = 0
    for quadro in QUADROS:
        resposta = cliente.obter(URL_BASE + quadro)
        cabecalho = resposta.headers.get("Last-Modified")
        if resposta.status_code != 200 or not cabecalho:
            falhas += 1
            continue
        if not resposta.content.startswith(b"\x89PNG"):
            raise ErroSchema(f"{quadro} não é PNG — formato do radar mudou?")
        ts = parsedate_to_datetime(cabecalho)
        marca_frescor = max(marca_frescor, ts) if marca_frescor else ts
        blobs.append(
            BlobNovo(
                caminho=f"radar/{ts:%Y/%m}/{ts:%Y%m%d_%H%M%S}.png",
                ts=ts,
                conteudo=resposta.content,
                meta={"bounds": BOUNDS, "arquivo_origem": quadro},
            )
        )
    if falhas == len(QUADROS):
        raise ErroSchema("nenhum quadro do radar disponível")
    return ResultadoColeta(blobs=blobs, marca_frescor=marca_frescor)


FONTE = FonteConfig(
    slug="radar_sumare",
    nome="Radar meteorológico do Sumaré",
    orgao="Prefeitura do Rio / Alerta Rio",
    url=URL_BASE,
    bloco="A",
    criticidade=3,
    cadencia=timedelta(minutes=5),
    tolerancia_frescor=timedelta(minutes=30),
    coletar=coletar,
)
