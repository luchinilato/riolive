"""Detector de linha parada — o ativo original do projeto virando evento.

A cada rodada (5 min): linhas planejadas AGORA (GTFS) sem nenhum veículo há 40+
min viram `evento` tipo `linha_parada` (vigente, um por linha); quando a linha
volta a circular, o evento é fechado. Com o GPS fora do ar o detector não abre
nem fecha nada — a máquina de saúde é a trava contra falso positivo em massa.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, text, update

from riolive.db import sessao
from riolive.mobilidade import detectar_paradas, gps_saudavel, linhas_agora
from riolive.modelos import Evento

logger = logging.getLogger(__name__)

SLUG_FONTE = "detector_linha_parada"
SEVERIDADE = 2


def _garantir_fonte(s: Any) -> int:
    linha = s.execute(
        text(
            "INSERT INTO fonte (slug, nome, orgao, url, bloco, criticidade, cadencia_segundos) "
            "VALUES (:slug, 'Detector de linha parada (planejado × realizado)', 'riolive', "
            "'interno://detector', 'B', 4, 300) "
            "ON CONFLICT (slug) DO UPDATE SET nome = EXCLUDED.nome RETURNING id"
        ),
        {"slug": SLUG_FONTE},
    )
    return int(linha.scalar_one())


def rodar() -> dict[str, int]:
    """Executa uma rodada; retorna contadores (abertos, fechados, vigentes)."""
    agora = datetime.now(tz=UTC)
    with sessao() as s:
        if not gps_saudavel(s):
            logger.warning("GPS fora do ar: detector em espera (sem abrir/fechar eventos)")
            return {"abertos": 0, "fechados": 0, "vigentes": -1}

        fonte_id = _garantir_fonte(s)
        linhas = linhas_agora(s)
        paradas = {p.linha: p for p in detectar_paradas(linhas)}
        rodando = {li.linha for li in linhas if li.veiculos > 0}

        abertos_no_banco = (
            s.execute(select(Evento).where(Evento.tipo == "linha_parada", Evento.fim.is_(None)))
            .scalars()
            .all()
        )
        por_linha = {e.payload.get("linha"): e for e in abertos_no_banco if e.payload}

        fechados = 0
        for linha_gtfs, evento in por_linha.items():
            if linha_gtfs in rodando:
                s.execute(
                    update(Evento)
                    .where(Evento.inicio == evento.inicio, Evento.id == evento.id)
                    .values(fim=agora)
                )
                fechados += 1

        abertos = 0
        for nome_linha, parada in paradas.items():
            if nome_linha in por_linha and por_linha[nome_linha].fim is None:
                continue  # já aberto
            inicio = agora - timedelta(minutes=parada.minutos_sem_gps or 0)
            s.add(
                Evento(
                    tipo="linha_parada",
                    fonte_id=fonte_id,
                    severidade=SEVERIDADE,
                    inicio=inicio,
                    fim=None,
                    titulo=f"Linha {parada.linha} sem circular",
                    descricao=(
                        f"Planejada pra agora (frequência de {round(parada.headway_seg / 60)} min "
                        f"no GTFS), sem nenhum veículo com GPS há {parada.minutos_sem_gps} min. "
                        f"{parada.nome}"
                    ),
                    payload={"linha": parada.linha, "headway_seg": parada.headway_seg},
                    coletado_em=agora,
                )
            )
            abertos += 1

        vigentes = len(por_linha) - fechados + abertos
    logger.info("linha_parada: %s abertos, %s fechados, %s vigentes", abertos, fechados, vigentes)
    return {"abertos": abertos, "fechados": fechados, "vigentes": vigentes}
