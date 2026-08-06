"""Definições do Dagster: um job agregador pras fontes quentes (cadência ≤ 1 min,
mitiga o custo de um run por fonte por minuto) e um job + schedule por fonte fria.

O dead-man's switch pinga ao fim de cada rodada do agregador: se o daemon ou o
servidor morrerem, o healthchecks.io percebe o silêncio e alerta.
"""

from dagster import (
    DefaultScheduleStatus,
    Definitions,
    In,
    JobDefinition,
    Nothing,
    OpDefinition,
    OpExecutionContext,
    ScheduleDefinition,
    job,
    op,
)

from riolive.detectores import linha_parada
from riolive.fontes import FONTES
from riolive.ingestao.contrato import FonteConfig
from riolive.ingestao.execucao import executar_fonte
from riolive.saude import heartbeat
from riolive.snapshot import gravar_snapshot


def _fabricar_op(cfg: FonteConfig) -> OpDefinition:
    @op(name=f"coletar_{cfg.slug}", description=f"Coleta {cfg.nome}")
    def _coletar(context: OpExecutionContext) -> None:
        resumo = executar_fonte(cfg)
        context.log.info(
            "%s: estado=%s latencia=%sms inseridos=%s detalhe=%s",
            resumo.slug,
            resumo.estado,
            resumo.latencia_ms,
            resumo.inseridos,
            resumo.detalhe,
        )

    return _coletar


def _cron(cfg: FonteConfig) -> str:
    minutos = max(1, int(cfg.cadencia.total_seconds()) // 60)
    if minutos == 1:
        return "* * * * *"
    if minutos < 60:
        return f"*/{minutos} * * * *"
    return f"0 */{minutos // 60} * * *"


_quentes = [cfg for cfg in FONTES.values() if cfg.quente]
_frias = [cfg for cfg in FONTES.values() if not cfg.quente]


@op(ins={"apos": In(Nothing)})
def pingar_heartbeat(context: OpExecutionContext) -> None:
    heartbeat.pingar()
    context.log.debug("heartbeat ok")


def _fabricar_job_quentes() -> JobDefinition:
    ops_quentes = [_fabricar_op(cfg) for cfg in _quentes]

    @job(
        name="fontes_quentes",
        description="Fontes de cadência de 1 min, num run só (mitigação do polling do Dagster)",
    )
    def _job() -> None:
        pingar_heartbeat(apos=[op_coleta() for op_coleta in ops_quentes])

    return _job


def _fabricar_job_fria(cfg: FonteConfig) -> JobDefinition:
    op_coleta = _fabricar_op(cfg)

    @job(name=f"coleta_{cfg.slug}", description=f"Coleta {cfg.nome}")
    def _job() -> None:
        op_coleta()

    return _job


@op
def tirar_snapshot(context: OpExecutionContext) -> None:
    contadores = gravar_snapshot()
    context.log.info("snapshot: %s", contadores)


@job(name="snapshot_cidade", description="Fotografia resumida da cidade (replay da UI, fase 3)")
def _job_snapshot() -> None:
    tirar_snapshot()


@op
def detectar_linhas_paradas(context: OpExecutionContext) -> None:
    resultado = linha_parada.rodar()
    context.log.info("detector linha_parada: %s", resultado)


@job(
    name="detector_linha_parada",
    description="Planejado × realizado: abre/fecha eventos de linha sem circular",
)
def _job_linha_parada() -> None:
    detectar_linhas_paradas()


_job_quentes = _fabricar_job_quentes()
_jobs_frias = [_fabricar_job_fria(cfg) for cfg in _frias]

_schedules = [
    ScheduleDefinition(
        name="agenda_fontes_quentes",
        job=_job_quentes,
        cron_schedule="* * * * *",
        execution_timezone="America/Sao_Paulo",
        default_status=DefaultScheduleStatus.RUNNING,
    ),
    *[
        ScheduleDefinition(
            name=f"agenda_{cfg.slug}",
            job=job_fria,
            cron_schedule=_cron(cfg),
            execution_timezone="America/Sao_Paulo",
            default_status=DefaultScheduleStatus.RUNNING,
        )
        for cfg, job_fria in zip(_frias, _jobs_frias, strict=True)
    ],
    ScheduleDefinition(
        name="agenda_detector_linha_parada",
        job=_job_linha_parada,
        cron_schedule="*/5 * * * *",
        execution_timezone="America/Sao_Paulo",
        default_status=DefaultScheduleStatus.RUNNING,
    ),
    ScheduleDefinition(
        name="agenda_snapshot_cidade",
        job=_job_snapshot,
        cron_schedule="*/15 * * * *",
        execution_timezone="America/Sao_Paulo",
        default_status=DefaultScheduleStatus.RUNNING,
    ),
]

defs = Definitions(
    jobs=[_job_quentes, *_jobs_frias, _job_snapshot, _job_linha_parada],
    schedules=_schedules,
)
