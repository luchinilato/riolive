"""Detector de linha parada — o ativo original do projeto virando evento.

A cada rodada (5 min): linhas planejadas AGORA (GTFS) sem nenhum veículo há 40+
min viram `evento` tipo `linha_parada` (vigente, um por linha); quando a linha
volta a circular, o evento é fechado. Com o GPS fora do ar o detector não abre
nem fecha nada — a máquina de saúde é a trava contra falso positivo em massa.

O detector também **reporta a própria saúde**, porque aparece na página pública
de status como qualquer fonte. Sem isso ele ficava `desconhecido` pra sempre,
inclusive rodando bem (visto em 2026-08-07). Esperando o GPS ficar confiável é
`degradada` — o detector está de pé, quem não está é a entrada dele; e como isso
não é falha de rede, schema nem frescor, vai sem classe de falha. Não dispara
alerta: espera por GPS é estado normal, não incidente.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, text, update

from riolive.db import sessao
from riolive.mobilidade import detectar_paradas, gps_confiavel, linhas_agora
from riolive.modelos import Evento, SaudeFonte
from riolive.saude.controle import ControleSaude

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


def _registrar_saude(s: Any, fonte_id: int, agora: datetime, estado: str, detalhe: str) -> None:
    """Grava transição de estado do detector (só quando muda, como o executor faz)."""
    controle = ControleSaude(SLUG_FONTE)
    if controle.estado_anterior() == estado:
        return
    s.add(
        SaudeFonte(
            ts=agora,
            fonte_id=fonte_id,
            estado=estado,
            classe_falha=None,  # espera por dependência não é rede/schema/frescor
            latencia_ms=None,
            detalhe=detalhe,
        )
    )
    controle.gravar_estado(estado)
    logger.info("detector linha_parada: estado %s (%s)", estado, detalhe)


def rodar() -> dict[str, int]:
    """Executa uma rodada; retorna contadores (abertos, fechados, vigentes)."""
    agora = datetime.now(tz=UTC)
    with sessao() as s:
        # Antes da trava: a fonte precisa existir pra aparecer no status mesmo em espera
        fonte_id = _garantir_fonte(s)
        confiavel, motivo = gps_confiavel(s)
        if not confiavel:
            logger.warning("detector em espera: %s", motivo)
            _registrar_saude(s, fonte_id, agora, "degradada", f"em espera: {motivo}")
            return {"abertos": 0, "fechados": 0, "vigentes": -1}

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
        _registrar_saude(
            s,
            fonte_id,
            agora,
            "online",
            f"{len(linhas)} linhas planejadas agora, {vigentes} sem circular",
        )
    logger.info("linha_parada: %s abertos, %s fechados, %s vigentes", abertos, fechados, vigentes)
    return {"abertos": abertos, "fechados": fechados, "vigentes": vigentes}
