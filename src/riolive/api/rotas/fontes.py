"""GET /fontes — status público de todas as fontes (a página da transparência).

O uptime é reconstruído da máquina de estados (saude_fonte guarda transições):
pra cada dia dos últimos 30, o pior estado em vigor naquele dia; % de uptime =
fração do tempo OBSERVADO em `online` (honesto: antes da primeira coleta não há
dado, e isso aparece como "sem dado", não como 100%).
"""

from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from sqlalchemy import text

from riolive.db import sessao
from riolive.saude.controle import ControleSaude

rota = APIRouter(tags=["fontes"])

TZ_RIO = ZoneInfo("America/Sao_Paulo")
GRAVIDADE = {"online": 0, "degradada": 1, "congelada": 2, "fora": 3}
DIAS_BARRAS = 30

# Quantas cadências uma fonte pode ficar sem ser coletada antes de o estado
# gravado deixar de valer. Três tolera dois ciclos perdidos — abaixo disso, um
# atraso normal viraria alarme.
CADENCIAS_ATE_VENCER = 3
# Piso, para não acusar fonte de 1 min por causa de 2 min de atraso.
VENCIMENTO_MINIMO_S = 600


def _vencido(
    cadencia_s: int,
    ultima_coleta: datetime | None,
    agora: datetime,
    ultima_transicao: datetime | None = None,
) -> int | None:
    """Segundos desde a última coleta, se a leitura de estado já venceu.

    O estado em `saude_fonte` é a ÚLTIMA TRANSIÇÃO, e transição só acontece
    quando o estado muda. Fonte saudável há uma semana não gera registro nenhum,
    então "online" continua verdadeiro no banco mesmo depois de o pipeline
    inteiro morrer — foi o que fez a página anunciar 20 de 21 fontes no ar com
    a coleta parada havia 6 h, em 2026-08-07.

    Sem notícia (`None`) também vence: preferimos dizer que não sabemos.

    A data da última TRANSIÇÃO serve de reserva, e a assimetria é o ponto:
    ausência de transição não prova nada, mas transição recente prova coleta
    recente — só se grava transição depois de coletar. Sem essa reserva, uma
    fonte de cadência diária apareceria como desconhecida por 24 h depois de
    todo deploy, porque o carimbo no Redis ainda não existiria.
    """
    limite = max(CADENCIAS_ATE_VENCER * cadencia_s, VENCIMENTO_MINIMO_S)
    visto = max([d for d in (ultima_coleta, ultima_transicao) if d], default=None)
    if visto is None:
        return None
    idade = int((agora - visto).total_seconds())
    return idade if idade > limite else 0


def _uptime_por_fonte(transicoes: Sequence[Any]) -> dict[int, dict[str, Any]]:
    """Reconstrói, por fonte: pior estado por dia (30 dias) e % do tempo em online."""
    por_fonte: dict[int, list[Any]] = defaultdict(list)
    for linha in transicoes:
        por_fonte[linha.fonte_id].append(linha)

    agora = datetime.now(tz=UTC)
    hoje_rio = agora.astimezone(TZ_RIO).date()
    saida: dict[int, dict[str, Any]] = {}
    for fonte_id, eventos in por_fonte.items():
        eventos.sort(key=lambda e: e.ts)
        # % de uptime sobre o tempo observado (da 1ª transição até agora)
        online_s = 0.0
        for atual, proximo in zip(eventos, [*eventos[1:], None], strict=False):
            fim = proximo.ts if proximo else agora
            if atual.estado == "online":
                online_s += (fim - atual.ts).total_seconds()
        observado_s = (agora - eventos[0].ts).total_seconds()
        uptime_pct = round(100 * online_s / observado_s, 1) if observado_s > 0 else None

        dias = []
        for atras in range(DIAS_BARRAS - 1, -1, -1):
            dia = hoje_rio - timedelta(days=atras)
            inicio_dia = datetime.combine(dia, datetime.min.time(), tzinfo=TZ_RIO)
            fim_dia = inicio_dia + timedelta(days=1)
            herdado = None
            pior = None
            for e in eventos:
                if e.ts < inicio_dia:
                    herdado = e.estado
                elif e.ts < fim_dia:
                    pior = (
                        e.estado
                        if pior is None
                        else max(pior, e.estado, key=lambda s: GRAVIDADE[s])
                    )
            candidatos = [s for s in (herdado, pior) if s is not None]
            dominante = max(candidatos, key=lambda s: GRAVIDADE[s]) if pior else (herdado or None)
            dias.append(dominante)
        saida[fonte_id] = {"uptime_pct": uptime_pct, "dias": dias}
    return saida


@rota.get("/fontes")
def listar_fontes() -> list[dict[str, Any]]:
    with sessao() as s:
        linhas = s.execute(
            text(
                """
                SELECT f.id, f.slug, f.nome, f.orgao, f.bloco, f.criticidade,
                       f.cadencia_segundos, u.estado, u.classe_falha, u.ts, u.detalhe
                FROM fonte f
                LEFT JOIN LATERAL (
                    SELECT estado, classe_falha, ts, detalhe FROM saude_fonte
                    WHERE fonte_id = f.id ORDER BY ts DESC LIMIT 1
                ) u ON TRUE
                ORDER BY f.bloco, f.slug
                """
            )
        ).all()
        transicoes = s.execute(
            text("SELECT fonte_id, ts, estado FROM saude_fonte ORDER BY fonte_id, ts")
        ).all()
    uptime = _uptime_por_fonte(transicoes)
    agora = datetime.now(tz=UTC)
    saida = []
    for linha in linhas:
        ultima = ControleSaude(linha.slug).ultima_coleta()
        atraso = _vencido(linha.cadencia_segundos, ultima, agora, linha.ts)
        venceu = atraso is None or atraso > 0
        saida.append(
            {
                "slug": linha.slug,
                "nome": linha.nome,
                "orgao": linha.orgao,
                "bloco": linha.bloco,
                "criticidade": linha.criticidade,
                "cadencia_segundos": linha.cadencia_segundos,
                # Estado vencido não é o último conhecido: é desconhecido.
                "estado": "desconhecido" if venceu else (linha.estado or "desconhecido"),
                "estado_gravado": linha.estado,
                "classe_falha": None if venceu else linha.classe_falha,
                "desde": linha.ts.isoformat() if linha.ts else None,
                "ultima_coleta": ultima.isoformat() if ultima else None,
                "detalhe": (
                    "Sem coleta registrada — não sabemos o estado desta fonte."
                    if atraso is None
                    else f"Última coleta há {atraso // 60} min, acima do previsto para a cadência."
                    if venceu
                    else linha.detalhe
                ),
                "uptime_pct": uptime.get(linha.id, {}).get("uptime_pct"),
                "dias": uptime.get(linha.id, {}).get("dias", [None] * DIAS_BARRAS),
            }
        )
    return saida


@rota.get("/fontes/pipeline")
def pipeline() -> dict[str, Any]:
    """Sinal de vida da ingestão, separado do estado das fontes.

    Existe porque "20 de 21 fontes online" é verdade sobre as origens e não diz
    nada sobre nós: em 2026-08-07 a página exibiu exatamente isso com o Dagster
    parado havia 6 h. Uma fonte pode cair sozinha; se TODAS pararem de ser
    coletadas ao mesmo tempo, o problema é nosso, e o painel precisa saber
    dizer de quem é a culpa.
    """
    with sessao() as s:
        fontes = s.execute(
            text(
                """
                SELECT f.slug, f.cadencia_segundos, u.ts
                FROM fonte f
                LEFT JOIN LATERAL (
                    SELECT ts FROM saude_fonte WHERE fonte_id = f.id ORDER BY ts DESC LIMIT 1
                ) u ON TRUE
                """
            )
        ).all()

    agora = datetime.now(tz=UTC)
    coletas = [
        (f.slug, ControleSaude(f.slug).ultima_coleta(), f.cadencia_segundos, f.ts) for f in fontes
    ]
    # Mesma reserva de `_vencido`: transição recente prova coleta recente.
    recentes = [max([d for d in (q, tr) if d]) for _, q, _, tr in coletas if q or tr]
    vencidas = sum(1 for _, q, cad, tr in coletas if _vencido(cad, q, agora, tr) != 0)

    ultima = max(recentes, default=None)
    # O relógio do pipeline é a fonte MAIS RÁPIDA: se a ingestão roda, quem
    # coleta de minuto em minuto carimba de minuto em minuto. Exigir que todas
    # as fontes vençam deixaria "vivo" verdadeiro com 18 de 19 paradas — que foi
    # a primeira versão desta conta, e repetiria o erro que ela veio corrigir.
    mais_rapida = min((cad for _, _, cad, _ in coletas), default=0)
    limite = max(CADENCIAS_ATE_VENCER * mais_rapida, VENCIMENTO_MINIMO_S)
    idade = int((agora - ultima).total_seconds()) if ultima else None
    return {
        "vivo": idade is not None and idade <= limite,
        "ultima_coleta": ultima.isoformat() if ultima else None,
        "ha_segundos": idade,
        "fontes_total": len(coletas),
        "fontes_vencidas": vencidas,
        "detalhe": (
            "Nenhuma fonte foi coletada recentemente — a ingestão está parada, "
            "e o estado das fontes abaixo é o último conhecido, não o de agora."
            if idade is None or idade > limite
            else None
        ),
    }
