"""Status das linhas do MetrôRio (fornecedor terceiro — frágil, monitorar).

O token Bearer vive hardcoded no JS público do site (catálogo, exp. 2051); em
vez de congelá-lo aqui, ele é re-extraído do script a cada coleta — sobrevive a
rotação. Só status ANORMAL vira evento (vigente por linha); a volta ao normal
encerra o evento. `updatedAt` da API é lixo (2024): frescor não se aplica.

**A API bloqueia o IP do nosso VPS.** Medido em 2026-08-07: o site
(`metrorio.com.br`) responde 200 do servidor, mas `api.ondeestameutrem.metrorio.app`
devolve 403 com `server: awselb/2.0` — WAF da AWS barrando a faixa do datacenter,
não o nosso cliente. Da máquina de casa a mesma coleta passa e devolve as três
linhas. Não é o caso do COR (lá era o handshake TLS do httpx, e `exige_libcurl`
resolveu): aqui curl e httpx tomam 403 igual. Por isso o 403 entra como falha de
rede — a fonte fica fora por bloqueio da origem, que é o que de fato acontece, e
volta sozinha se a faixa sair da lista.
"""

import json
import re
from datetime import UTC, datetime, timedelta

from riolive.fontes.comum import erro_de_status
from riolive.ingestao.contrato import ErroSchema, EventoNovo, FonteConfig, ResultadoColeta
from riolive.ingestao.fetcher import ClienteHttp

URL_SCRIPT = "https://www.metrorio.com.br/Content/js/situacao-linhas/script.js"
URL_STATUS = "https://api.ondeestameutrem.metrorio.app/v1/StatusLinha"
RE_TOKEN = re.compile(r"token:\s*'([^']+)'")


def _severidade(status: str) -> int:
    normalizado = status.lower()
    if "paralisad" in normalizado or "interromp" in normalizado:
        return 4
    if "parcial" in normalizado or "lentid" in normalizado or "reduzid" in normalizado:
        return 3
    return 2


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    script = cliente.obter(URL_SCRIPT)
    if script.status_code != 200:
        raise erro_de_status(script.status_code, "script do site do MetrôRio")
    achado = RE_TOKEN.search(script.text)
    if not achado:
        raise ErroSchema("token não encontrado no script do site — formato mudou")

    resposta = cliente.obter(URL_STATUS, headers={"Authorization": f"Bearer {achado.group(1)}"})
    if resposta.status_code != 200:
        raise erro_de_status(resposta.status_code, "StatusLinha")
    try:
        linhas = resposta.json()
    except json.JSONDecodeError as exc:
        raise ErroSchema(f"resposta não é JSON: {exc}") from exc
    if not isinstance(linhas, list) or not linhas:
        raise ErroSchema("StatusLinha sem lista de linhas")

    agora = datetime.now(tz=UTC)
    eventos: list[EventoNovo] = []
    for linha in linhas:
        numero = linha.get("linha")
        status = str(linha.get("status") or "").strip()
        if numero is None or not status:
            raise ErroSchema(f"registro sem linha/status: {linha}")
        tipo = f"metro_l{numero}"
        if status.lower() == "normal":
            eventos.append(
                EventoNovo(
                    tipo=tipo,
                    severidade=1,
                    inicio=agora,
                    titulo=f"Linha {numero} normalizada",
                    encerrar=True,
                )
            )
        else:
            eventos.append(
                EventoNovo(
                    tipo=tipo,
                    severidade=_severidade(status),
                    inicio=agora,
                    titulo=f"Metrô Linha {numero}: {status}",
                    payload={"linha": numero, "status": status},
                    vigente=True,
                )
            )
    return ResultadoColeta(eventos=eventos)


FONTE = FonteConfig(
    slug="metro_rio",
    nome="Status das linhas do MetrôRio",
    orgao="MetrôRio (via fornecedor)",
    url=URL_STATUS,
    bloco="B",
    criticidade=3,
    cadencia=timedelta(minutes=5),
    tolerancia_frescor=timedelta(days=365),  # status parado é o normal
    coletar=coletar,
)
