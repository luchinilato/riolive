"""Focos de calor do INPE (programa Queimadas), CSV nacional a cada 10 min.

O CSV só tem lat, lon, satélite e data (UTC) — sem recorte de município: o filtro
do Rio é espacial, em duas etapas: bbox metropolitano no parser (barato) e
`exigir_bairro` na gravação (point-in-polygon contra a dimensão bairro).

A cada rodada lemos os N arquivos mais recentes da listagem: o mais novo às vezes
ainda está vazio/incompleto quando publicado, e o dedup natural de evento
(tipo, inicio, h3) absorve a releitura.
"""

import csv
import io
import re
from datetime import UTC, datetime, timedelta

from riolive.fontes.comum import coordenada_plausivel
from riolive.ingestao.contrato import (
    ErroSchema,
    EventoNovo,
    FonteConfig,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp

URL_LISTAGEM = "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/10min/"
ARQUIVOS_POR_RODADA = 3  # 30 min de cobertura; releitura é deduplicada
PADRAO_ARQUIVO = re.compile(r'href="(focos_10min_(\d{8})_(\d{4})\.csv)"')


def _arquivos_recentes(html: str) -> list[tuple[str, datetime]]:
    encontrados = [
        (nome, datetime.strptime(f"{data}{hora}", "%Y%m%d%H%M").replace(tzinfo=UTC))
        for nome, data, hora in PADRAO_ARQUIVO.findall(html)
    ]
    if not encontrados:
        raise ErroSchema("listagem do INPE sem arquivos focos_10min_*.csv")
    return sorted(encontrados, key=lambda par: par[1])[-ARQUIVOS_POR_RODADA:]


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    listagem = cliente.obter(URL_LISTAGEM)
    if listagem.status_code != 200:
        raise ErroSchema(f"HTTP {listagem.status_code} na listagem do INPE")
    arquivos = _arquivos_recentes(listagem.text)

    eventos: list[EventoNovo] = []
    for nome, _ts_arquivo in arquivos:
        resposta = cliente.obter(URL_LISTAGEM + nome)
        if resposta.status_code != 200:
            raise ErroSchema(f"HTTP {resposta.status_code} em {nome}")
        leitor = csv.DictReader(io.StringIO(resposta.text))
        if leitor.fieldnames is None or "lat" not in leitor.fieldnames:
            raise ErroSchema(f"{nome} sem o cabeçalho lat,lon,satelite,data")
        for linha in leitor:
            lat, lon = float(linha["lat"]), float(linha["lon"])
            if not coordenada_plausivel(lat, lon):
                continue  # fora da região metropolitana: 99.9% do CSV nacional
            satelite = linha["satelite"].strip()
            ts = datetime.fromisoformat(linha["data"].strip()).replace(tzinfo=UTC)
            eventos.append(
                EventoNovo(
                    tipo="foco_calor",
                    severidade=2,
                    inicio=ts,
                    fim=ts,  # detecção pontual, não um estado vigente
                    titulo=f"Foco de calor ({satelite})",
                    lat=lat,
                    lon=lon,
                    payload={"satelite": satelite},
                    exigir_bairro=True,  # filtro de município que o CSV não tem
                )
            )

    # Frescor = idade do arquivo mais novo do INPE, não dos focos: zero foco no Rio
    # é o estado normal, não fonte congelada
    return ResultadoColeta(eventos=eventos, marca_frescor=arquivos[-1][1])


FONTE = FonteConfig(
    slug="queimadas_inpe",
    nome="Focos de calor (INPE Queimadas)",
    orgao="INPE",
    url=URL_LISTAGEM,
    bloco="A",
    criticidade=3,
    cadencia=timedelta(minutes=10),
    tolerancia_frescor=timedelta(hours=1),
    coletar=coletar,
)
