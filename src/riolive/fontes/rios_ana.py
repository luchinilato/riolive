"""Nível dos rios urbanos via telemetria da ANA (achado da varredura de 2026-08-05).

4 estações fluviométricas dentro da cidade (coordenadas do HidroInventario da
própria ANA, 2026-08-06). XML .asmx com o typo histórico no nome do elemento
(`DadosHidrometereologicos`), DataHora em hora local ingênua, mais novo primeiro,
15/15 min. Nível em cm: complementa o pluviômetro no painel de enchente.

O serviço é frágil (timeouts de SQL, estação sem dado por dias — a Acari estava
muda em 06/08): uma estação falhar não derruba a coleta; só falha se TODAS
falharem ou nenhuma trouxer dado.
"""

import logging
from datetime import datetime, timedelta

from defusedxml import ElementTree

from riolive.fontes.comum import TZ_RIO, local_para_utc
from riolive.ingestao.contrato import (
    ErroSchema,
    FonteConfig,
    LocalNovo,
    MedicaoNova,
    ResultadoColeta,
)
from riolive.ingestao.fetcher import ClienteHttp, ErroRede

logger = logging.getLogger(__name__)

URL = "https://telemetriaws1.ana.gov.br/ServiceANA.asmx/DadosHidrometeorologicos"

# codigo ANA → (nome de exibição, rio, lat, lon) — HidroInventario, 2026-08-06
ESTACOES = {
    "59305027": ("Acari", "Rio Acari", -22.8225, -43.35),
    "59305035": ("Estrada Velha da Pavuna", "Rio Faria-Timbó", -22.8731, -43.2681),
    "59305055": ("São Cristóvão", "Rio Maracanã", -22.9106, -43.2214),
    "59305071": ("Capela Mayrink", "Rio Tijuca", -22.9568, -43.2775),
}


def _interpretar_xml(conteudo: bytes, codigo: str) -> list[MedicaoNova]:
    try:
        raiz = ElementTree.fromstring(conteudo)
    except ElementTree.ParseError as exc:
        raise ErroSchema(f"XML inválido da estação {codigo}: {exc}") from exc

    medicoes: list[MedicaoNova] = []
    for elemento in raiz.iter():
        if not str(elemento.tag).endswith("DadosHidrometereologicos"):
            continue
        campos = {str(filho.tag).split("}")[-1]: (filho.text or "").strip() for filho in elemento}
        nivel = campos.get("Nivel")
        data_hora = campos.get("DataHora")
        if not nivel or not data_hora:
            continue  # leitura sem nível (só chuva/vazão) não vira medição de rio
        ts = local_para_utc(datetime.fromisoformat(data_hora))
        medicoes.append(
            MedicaoNova(
                codigo_local=codigo,
                metrica="nivel_rio_cm",
                ts=ts,
                valor=float(nivel),
                payload={
                    "chuva": campos.get("Chuva") or None,
                    "vazao": campos.get("Vazao") or None,
                },
            )
        )
    return medicoes


def coletar(cliente: ClienteHttp) -> ResultadoColeta:
    agora = datetime.now(tz=TZ_RIO)
    janela = {
        "dataInicio": (agora - timedelta(days=1)).strftime("%d/%m/%Y"),
        "dataFim": agora.strftime("%d/%m/%Y"),
    }

    locais = [
        LocalNovo(
            codigo_externo=codigo,
            nome=f"{nome} ({rio})",
            tipo="estacao_rio",
            lat=lat,
            lon=lon,
            extra={"rio": rio},
        )
        for codigo, (nome, rio, lat, lon) in ESTACOES.items()
    ]

    medicoes: list[MedicaoNova] = []
    falhas_rede: list[str] = []
    for codigo in ESTACOES:
        try:
            resposta = cliente.obter(URL, params={"codEstacao": codigo, **janela})
        except ErroRede as exc:
            # Serviço da ANA derruba estação individual com timeout de SQL:
            # tolera parcial, só derruba a coleta se todas falharem
            logger.warning("estação %s inalcançável: %s", codigo, exc)
            falhas_rede.append(codigo)
            continue
        if resposta.status_code != 200:
            falhas_rede.append(codigo)
            continue
        medicoes.extend(_interpretar_xml(resposta.content, codigo))

    if len(falhas_rede) == len(ESTACOES):
        raise ErroRede(f"todas as {len(ESTACOES)} estações da ANA inalcançáveis")
    if not medicoes:
        raise ErroSchema("nenhuma estação da ANA retornou leitura de nível na janela")

    return ResultadoColeta(
        medicoes=medicoes,
        locais=locais,
        marca_frescor=max(m.ts for m in medicoes),
    )


FONTE = FonteConfig(
    slug="rios_ana",
    nome="Nível de rios urbanos (ANA/INEA)",
    orgao="ANA — Agência Nacional de Águas",
    url=URL,
    bloco="A",
    criticidade=4,
    cadencia=timedelta(minutes=15),
    tolerancia_frescor=timedelta(hours=2),
    coletar=coletar,
)
