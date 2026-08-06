"""Registro das fontes ativas. Um módulo por fonte, exportando FONTE: FonteConfig."""

from riolive.fontes import alerta_rio, estagio_cor, gps_sppo, openaq
from riolive.ingestao.contrato import FonteConfig

FONTES: dict[str, FonteConfig] = {
    cfg.slug: cfg
    for cfg in (
        alerta_rio.FONTE,
        gps_sppo.FONTE,
        estagio_cor.FONTE,
        openaq.FONTE,
    )
}
