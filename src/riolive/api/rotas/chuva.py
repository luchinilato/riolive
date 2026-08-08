"""Chuva: leitura por estação agora e a climatologia que dá escala ao número."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from riolive.api.zonas import FILTRO_SQL, ZonaQuery, valor
from riolive.db import sessao
from riolive.fontes.comum import TZ_RIO

rota = APIRouter(tags=["chuva"])

METRICAS_TABELA = ("chuva_15min", "chuva_1h", "chuva_24h")


@rota.get("/chuva/estacoes")
def estacoes_chuva(zona: ZonaQuery = None) -> list[dict[str, Any]]:
    with sessao() as s:
        linhas = s.execute(
            text(
                f"""
                SELECT l.id, l.nome, b.nome bairro, r.nome ra, r.zona,
                       ST_Y(l.geom) lat, ST_X(l.geom) lon,
                       u.metrica, u.valor, u.ts
                FROM local l
                JOIN fonte f ON f.id = l.fonte_id AND f.slug = 'alerta_rio'
                LEFT JOIN bairro b ON b.id = l.bairro_id
                LEFT JOIN ra r ON r.id = l.ra_id
                LEFT JOIN LATERAL (
                    SELECT metrica, valor, ts FROM medicao
                    WHERE local_id = l.id
                      AND metrica IN ('chuva_15min', 'chuva_1h', 'chuva_24h')
                      AND ts > now() - interval '3 hours'
                    ORDER BY ts DESC LIMIT 6
                ) u ON TRUE
                WHERE {FILTRO_SQL}
                ORDER BY l.id
                """
            ),
            {"zona": valor(zona)},
        ).all()
    por_estacao: dict[int, dict[str, Any]] = {}
    for linha in linhas:
        est = por_estacao.setdefault(
            linha.id,
            {
                "id": linha.id,
                "nome": linha.nome,
                "bairro": linha.bairro,
                "ra": linha.ra,
                "zona": linha.zona,
                "lat": linha.lat,
                "lon": linha.lon,
                "leituras": {},
                "ts": None,
            },
        )
        if linha.metrica and linha.metrica not in est["leituras"]:
            est["leituras"][linha.metrica] = linha.valor
            est["ts"] = max(est["ts"], linha.ts) if est["ts"] else linha.ts
    return [
        {**est, "ts": est["ts"].isoformat() if est["ts"] else None} for est in por_estacao.values()
    ]


MESES = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)

# A comparação é sempre "mesmos dias do mês, anos diferentes". Comparar 7 dias
# de agosto contra agostos inteiros daria "34% da média" todo início de mês —
# um número que parece seca e é só calendário.
SQL_CLIMATOLOGIA = f"""
    WITH diario AS (
        SELECT (d.dia AT TIME ZONE 'America/Sao_Paulo')::date AS data, d.local_id, d.mm
        FROM chuva_dia_estacao d
        JOIN local l ON l.id = d.local_id
        JOIN fonte f ON f.id = l.fonte_id AND f.slug = 'alerta_rio'
        LEFT JOIN ra r ON r.id = l.ra_id
        -- O recorte entra aqui, antes da média: filtrar depois compararia a
        -- chuva da zona deste ano com a média da cidade nos anteriores.
        WHERE {FILTRO_SQL}
        -- Dia cheio são 96 leituras (uma a cada 15 min). Abaixo de 3/4 disso o
        -- total do dia é um piso, não uma medida: entra como chuva menor do que
        -- foi, e puxa a média histórica para baixo sem que nada acuse.
          AND d.leituras >= 72
    ),
    por_estacao AS (
        SELECT EXTRACT(YEAR FROM data)::int AS ano, local_id,
               sum(mm) AS mm, count(*) AS dias
        FROM diario
        WHERE EXTRACT(MONTH FROM data) = :mes
          AND EXTRACT(DAY FROM data) <= :dia_ate
        GROUP BY 1, 2
    )
    SELECT ano, avg(mm) AS mm, count(*) AS estacoes, max(dias) AS dias
    FROM por_estacao
    GROUP BY ano
    ORDER BY ano
"""


@rota.get("/chuva/climatologia")
def climatologia(zona: ZonaQuery = None) -> dict[str, Any]:
    """Chuva do mês corrente contra o mesmo recorte de dias nos anos anteriores.

    "Chuva da cidade" é a **média** das estações, não a soma: somar 33
    pluviômetros mede a rede, não a cidade. Estação sem leitura no período fica
    de fora do próprio ano, e o número de estações vai na resposta porque a rede
    cresceu de 26 (1997) para 33 (2013) e a comparação tem que assumir isso.

    Com `?zona=`, a mesma conta sobre os pluviômetros daquela zona — 4 a 15
    estações em vez de 33. O recorte vale para os dois lados da comparação, e
    `estacoes` na resposta continua dizendo sobre quantos a média foi feita.
    """
    hoje = datetime.now(TZ_RIO).date()
    with sessao() as s:
        linhas = s.execute(
            text(SQL_CLIMATOLOGIA),
            {"mes": hoje.month, "dia_ate": hoje.day, "zona": valor(zona)},
        ).all()

    serie = [
        {
            "ano": linha.ano,
            "mm": round(float(linha.mm), 1),
            "estacoes": linha.estacoes,
            "dias": linha.dias,
        }
        for linha in linhas
    ]
    atual = next((p for p in serie if p["ano"] == hoje.year), None)
    anteriores = [p for p in serie if p["ano"] != hoje.year]

    recorte = f" da Zona {zona.value.capitalize()}" if zona else ""
    resposta: dict[str, Any] = {
        "mes": hoje.month,
        "dia_ate": hoje.day,
        "periodo": f"1 a {hoje.day} de {MESES[hoje.month - 1]}",
        "zona": zona.value if zona else None,
        "atual": atual,
        "serie": serie,
        "historico": None,
        "percentual": None,
        "posicao": None,
        "lacuna": None,
        "metodologia": (
            f"Média dos pluviômetros do Alerta Rio{recorte}, somando o acumulado de 15 min "
            f"de 1 a {hoje.day} de {MESES[hoje.month - 1]}. O dia de hoje ainda está em curso."
        ),
    }
    if not anteriores:
        resposta["ausencia"] = "Sem histórico deste mês na série."
        return resposta

    anos = [p["ano"] for p in anteriores]
    media = sum(p["mm"] for p in anteriores) / len(anteriores)
    resposta["historico"] = {
        "media_mm": round(media, 1),
        "de": min(anos),
        "ate": max(anos),
        "anos": len(anteriores),
    }
    # Anos sem dado entre o começo da série e hoje — a origem pública parou em
    # 2024-06 e a coleta ao vivo só começou depois, então há um vão real a dizer.
    faltando = sorted(set(range(min(anos), hoje.year)) - set(anos))
    if faltando:
        resposta["lacuna"] = {"anos": faltando}

    if not atual:
        resposta["ausencia"] = f"Sem leitura nossa de {MESES[hoje.month - 1]} deste ano."
    elif atual["dias"] < hoje.day:
        # Ano corrente com menos dias medidos que o recorte: o total não é
        # comparável com anos completos, e dizer "X% da média" seria mentira
        # aritmeticamente correta.
        resposta["ausencia"] = (
            f"Medimos {atual['dias']} dos {hoje.day} dias do período — "
            "a comparação com a média histórica só vale quando o mês estiver coberto."
        )
    elif atual:
        resposta["percentual"] = round(100 * atual["mm"] / media) if media else None
        menores = sum(1 for p in anteriores if p["mm"] < atual["mm"])
        total = len(anteriores) + 1
        seco = menores < total / 2
        resposta["posicao"] = {
            "rank": menores + 1 if seco else total - menores,
            "total": total,
            "sentido": "mais seco" if seco else "mais chuvoso",
        }
    return resposta
