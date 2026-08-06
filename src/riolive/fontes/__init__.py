"""Registro das fontes ativas. Um módulo por fonte, exportando FONTE: FonteConfig."""

from riolive.fontes import (
    aguas_rio,
    alerta_rio,
    ceu_adsb,
    estagio_cor,
    gps_brt,
    gps_sppo,
    jogos,
    metro_rio,
    openaq,
    openmeteo,
    queimadas_inpe,
    radar_sumare,
    rios_ana,
    transito_tomtom,
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
        ceu_adsb.FONTE,
        metro_rio.FONTE,
        jogos.FONTE,
        aguas_rio.FONTE,
        transito_tomtom.FONTE,
    )
}
