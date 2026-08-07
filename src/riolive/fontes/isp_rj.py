"""Estatísticas de segurança do ISP-RJ — mensal por CISP, série desde 2003.

O CSV inteiro vem a cada coleta (semanal): filtramos as CISPs da capital
(regiao = Capital), somamos por mês e emitimos TODA a série — o dedup por PK
absorve o repetido, e a primeira coleta é um backfill de 23 anos de graça.
Métricas viram medições mensais no local agregado `capital` (ts = dia 1º).

Pegadinha do catálogo confirmada: usar o host COM www (sem www o TLS falha).
"""

import csv
import io
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from riolive.ingestao.contrato import (
    ErroSchema,
    FonteConfig,
    LocalNovo,
    MedicaoNova,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp

URL = "https://www.ispdados.rj.gov.br/Arquivos/BaseDPEvolucaoMensalCisp.csv"
UTC = ZoneInfo("UTC")

# coluna do CSV → metrica no vocabulário
METRICAS_ISP = {
    "letalidade_violenta": "isp_letalidade_violenta",
    "hom_doloso": "isp_hom_doloso",
    "roubo_rua": "isp_roubo_rua",
    "roubo_veiculo": "isp_roubo_veiculo",
    "roubo_celular": "isp_roubo_celular",
    "estupro": "isp_estupro",
}
CODIGO_LOCAL = "capital"


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    resposta = cliente.obter(URL)
    if resposta.status_code != 200:
        raise ErroSchema(f"HTTP {resposta.status_code} no CSV do ISP")
    texto = resposta.content.decode("latin-1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    if leitor.fieldnames is None or "cisp" not in leitor.fieldnames:
        raise ErroSchema("CSV sem o cabeçalho esperado (cisp;mes;ano;...)")
    faltando = [c for c in METRICAS_ISP if c not in leitor.fieldnames]
    if faltando:
        raise ErroSchema(f"colunas sumiram do CSV: {faltando}")

    somas: dict[tuple[int, int], dict[str, float]] = {}
    for linha in leitor:
        if (linha.get("regiao") or "").strip() != "Capital":
            continue
        chave = (int(linha["ano"]), int(linha["mes"]))
        acumulado = somas.setdefault(chave, dict.fromkeys(METRICAS_ISP.values(), 0.0))
        for coluna, metrica in METRICAS_ISP.items():
            bruto = (linha.get(coluna) or "").strip()
            if bruto:
                acumulado[metrica] += float(bruto)
    if not somas:
        raise ErroSchema("nenhuma linha da Capital no CSV")

    medicoes = [
        MedicaoNova(
            codigo_local=CODIGO_LOCAL,
            metrica=metrica,
            ts=datetime(ano, mes, 1, tzinfo=UTC),
            valor=valor,
        )
        for (ano, mes), metricas in somas.items()
        for metrica, valor in metricas.items()
    ]
    marca_frescor = max(m.ts for m in medicoes)
    locais = [
        LocalNovo(
            codigo_externo=CODIGO_LOCAL,
            nome="Município do Rio (CISPs da capital)",
            tipo="municipio",
            lat=-22.9068,
            lon=-43.1729,
        )
    ]
    return ResultadoColeta(medicoes=medicoes, locais=locais, marca_frescor=marca_frescor)


FONTE = FonteConfig(
    slug="isp_rj",
    nome="Estatísticas de segurança (ISP-RJ)",
    orgao="Instituto de Segurança Pública do RJ",
    url=URL,
    bloco="C",
    criticidade=2,
    cadencia=timedelta(days=7),
    tolerancia_frescor=timedelta(days=75),  # dado mensal com defasagem de divulgação
    coletar=coletar,
)
