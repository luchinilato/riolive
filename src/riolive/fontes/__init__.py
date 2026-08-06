"""Registro das fontes ativas. Um módulo por fonte, exportando FONTE: FonteConfig."""

from riolive.fontes import (
    alerta_rio,
    estagio_cor,
    gps_brt,
    gps_sppo,
    openaq,
    openmeteo,
    queimadas_inpe,
    radar_sumare,
    rios_ana,
)
from riolive.ingestao.contrato import FonteConfig

FONTES: dict[str, FonteConfig] = {
    cfg.slug: cfg
    for cfg in (
        alerta_rio.FONTE,
        gps_sppo.FONTE,
        gps_brt.FONTE,
        estagio_cor.FONTE,
        openaq.FONTE,
        rios_ana.FONTE,
        queimadas_inpe.FONTE,
        radar_sumare.FONTE,
        openmeteo.FONTE_TEMPO,
        openmeteo.FONTE_MAR,
    )
}
