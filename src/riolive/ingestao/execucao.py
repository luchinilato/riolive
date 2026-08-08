"""Executor de fonte: coleta → gravação → máquina de estados → alerta.

É o que os ops do Dagster chamam. Uma execução nunca levanta exceção por falha
da fonte — falha vira estado de saúde e alerta; exceção só por defeito nosso
(banco fora, bug de código), que aí sim deve estourar no Dagster.
"""

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from time import perf_counter

from pydantic import ValidationError

from riolive.db import sessao
from riolive.ingestao import gravacao
from riolive.ingestao.contrato import ErroSchema, FonteConfig, ResultadoColeta
from riolive.ingestao.fetcher import ClienteHttp, ErroRede
from riolive.modelos import SaudeFonte
from riolive.saude.alertas import alertar_transicao
from riolive.saude.controle import ControleSaude
from riolive.saude.maquina import avaliar, deve_alertar

logger = logging.getLogger(__name__)


@dataclass
class ResumoExecucao:
    slug: str
    estado: str
    classe_falha: str | None
    latencia_ms: int
    detalhe: str
    inseridos: dict[str, int] = field(default_factory=dict)


def executar_fonte(
    cfg: FonteConfig,
    cliente: ClienteHttp | None = None,
    controle: ControleSaude | None = None,
) -> ResumoExecucao:
    coletado_em = gravacao.agora_utc()
    controle = controle if controle is not None else ControleSaude(cfg.slug)
    proprio_cliente = cliente is None
    cliente = cliente if cliente is not None else ClienteHttp(libcurl=cfg.exige_libcurl)

    classe_erro: str | None = None
    detalhe_erro = ""
    resultado: ResultadoColeta | None = None
    t0 = perf_counter()
    try:
        resultado = cfg.coletar(cliente)
    except ErroRede as exc:
        classe_erro, detalhe_erro = "rede", str(exc)
    except (ErroSchema, ValidationError) as exc:
        classe_erro, detalhe_erro = "schema", str(exc)[:500]
    finally:
        if proprio_cliente:
            cliente.fechar()
    latencia_ms = int((perf_counter() - t0) * 1000)

    inseridos: dict[str, int] = {}
    atraso_frescor: timedelta | None = None
    if resultado is not None:
        with sessao() as s:
            fonte_id = gravacao.garantir_fonte(s, cfg)
            mapa_locais = gravacao.upsert_locais(s, fonte_id, resultado.locais)
            if resultado.medicoes:
                inseridos["medicoes"] = gravacao.inserir_medicoes(
                    s, fonte_id, resultado.medicoes, mapa_locais, coletado_em
                )
            if resultado.posicoes:
                inseridos["posicoes"] = gravacao.inserir_posicoes(
                    s, resultado.posicoes, coletado_em
                )
            if resultado.eventos:
                inseridos["eventos"] = gravacao.gravar_eventos(
                    s, fonte_id, resultado.eventos, coletado_em
                )
            if resultado.blobs:
                inseridos["blobs"] = gravacao.gravar_blobs(s, fonte_id, resultado.blobs)
            if resultado.previsoes:
                inseridos["previsoes"] = gravacao.inserir_previsoes(
                    s, resultado.previsoes, mapa_locais, coletado_em
                )
        if resultado.marca_frescor is not None:
            idade = coletado_em - resultado.marca_frescor
            if idade > cfg.tolerancia_frescor:
                atraso_frescor = idade - cfg.tolerancia_frescor

    if classe_erro == "rede":
        falhas = controle.registrar_falha_rede()
    else:
        falhas = 0
        controle.zerar_falhas_rede()

    # Antes de qualquer ramo: o carimbo diz que o pipeline passou por aqui, e é
    # o que separa "está no ar" de "estava no ar quando parou".
    controle.marcar_coleta(coletado_em)

    aval = avaliar(classe_erro, falhas, atraso_frescor)
    detalhe = detalhe_erro or aval.detalhe
    anterior = controle.estado_anterior()

    if aval.estado != anterior:
        with sessao() as s:
            fonte_id = gravacao.garantir_fonte(s, cfg)
            s.add(
                SaudeFonte(
                    ts=coletado_em,
                    fonte_id=fonte_id,
                    estado=aval.estado,
                    classe_falha=aval.classe_falha,
                    latencia_ms=latencia_ms,
                    detalhe=detalhe,
                )
            )
        controle.gravar_estado(aval.estado)
        if deve_alertar(anterior, aval) and controle.tentar_iniciar_cooldown():
            alertar_transicao(cfg.slug, anterior, aval.estado, aval.classe_falha, detalhe)

    logger.info("%s: %s (%s ms) %s", cfg.slug, aval.estado, latencia_ms, inseridos or detalhe)
    return ResumoExecucao(
        slug=cfg.slug,
        estado=aval.estado,
        classe_falha=aval.classe_falha,
        latencia_ms=latencia_ms,
        detalhe=detalhe,
        inseridos=inseridos,
    )
