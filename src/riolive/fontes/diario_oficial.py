"""Diário Oficial do Município — corpus da fase 3 (RAG), guardado como blob.

API JSON sem auth (upgrade sobre o plano, que supunha PDF cru): metadados por
edição + download do PDF por id. Coleta hoje e ontem (edições podem sair ao
longo do dia); fim de semana e feriado sem edição é normal — a tolerância de
frescor é de dias, não horas.
"""

import json
from datetime import datetime, timedelta

from riolive.blobs import armazem
from riolive.fontes.comum import TZ_RIO, local_para_utc
from riolive.ingestao.contrato import BlobNovo, ErroSchema, FonteConfig, ResultadoColeta
from riolive.ingestao.fetcher import ClienteHttp

URL_EDICOES = "https://doweb.rio.rj.gov.br/apifront/portal/edicoes/edicoes_from_data/"
URL_DOWNLOAD = "https://doweb.rio.rj.gov.br/apifront/portal/edicoes/download/{id}"


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    hoje = datetime.now(tz=TZ_RIO).date()
    blobs: list[BlobNovo] = []
    marca_frescor = None
    viu_resposta_valida = False

    for dia in (hoje, hoje - timedelta(days=1)):
        resposta = cliente.obter(URL_EDICOES, params={"data": dia.isoformat()})
        if resposta.status_code != 200:
            continue
        try:
            corpo = resposta.json()
        except json.JSONDecodeError as exc:
            raise ErroSchema(f"resposta não é JSON: {exc}") from exc
        if "itens" not in corpo:
            raise ErroSchema("resposta sem o campo `itens` — formato mudou")
        viu_resposta_valida = True

        for edicao in corpo["itens"] or []:
            ts = local_para_utc(datetime.combine(dia, datetime.min.time()))
            marca_frescor = max(marca_frescor, ts) if marca_frescor else ts
            sufixo = "_supl" if edicao.get("suplemento") else ""
            caminho = (
                f"diario_oficial/{dia:%Y/%m}/{dia.isoformat()}_ed{edicao.get('numero')}{sufixo}.pdf"
            )
            if armazem().existe(caminho):
                continue  # edição já no armazém: evita rebaixar ~30 MB a cada rodada
            pdf = cliente.obter(URL_DOWNLOAD.format(id=edicao["id"]))
            if pdf.status_code != 200 or not pdf.content.startswith(b"%PDF"):
                raise ErroSchema(f"download da edição {edicao['id']} não é PDF")
            blobs.append(
                BlobNovo(
                    caminho=caminho,
                    ts=ts,
                    conteudo=pdf.content,
                    meta={
                        "numero": edicao.get("numero"),
                        "paginas": edicao.get("paginas"),
                        "suplemento": edicao.get("suplemento"),
                        "id_edicao": edicao.get("id"),
                    },
                )
            )
    if not viu_resposta_valida:
        raise ErroSchema("nenhuma resposta válida do portal de edições")
    return ResultadoColeta(blobs=blobs, marca_frescor=marca_frescor)


FONTE = FonteConfig(
    slug="diario_oficial",
    nome="Diário Oficial do Município",
    orgao="Prefeitura do Rio",
    url=URL_EDICOES,
    bloco="E",
    criticidade=1,
    cadencia=timedelta(hours=6),
    tolerancia_frescor=timedelta(days=4),  # fim de semana/feriado sem edição é normal
    coletar=coletar,
)
