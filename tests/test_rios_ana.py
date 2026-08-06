"""Parser dos rios da ANA sobre XML real da estação Capela Mayrink (Rio Tijuca)."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from riolive.fontes import rios_ana
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp

XML_SEM_DADOS = (
    b'<?xml version="1.0" encoding="utf-8"?><DataTable xmlns="http://MRCS/">'
    b"<Error>Sem dados para esta esta\xc3\xa7\xc3\xa3o no per\xc3\xadodo!</Error></DataTable>"
)


def _coletar_com(respostas: dict[str, bytes]) -> rios_ana.ResultadoColeta:
    """Mocka o serviço devolvendo `respostas[codEstacao]` (default: sem dados)."""
    with respx.mock:

        def responder(request: httpx.Request) -> httpx.Response:
            codigo = request.url.params["codEstacao"]
            return httpx.Response(200, content=respostas.get(codigo, XML_SEM_DADOS))

        respx.get(url__startswith=rios_ana.URL).mock(side_effect=responder)
        with ClienteHttp() as cliente:
            return rios_ana.coletar(cliente)


def test_xml_real_vira_medicoes_de_nivel(fixtures: Path) -> None:
    xml = (fixtures / "ana_rio_tijuca.xml").read_bytes()
    resultado = _coletar_com({"59305071": xml})
    assert len(resultado.medicoes) == 6
    ultima = max(resultado.medicoes, key=lambda m: m.ts)
    assert ultima.metrica == "nivel_rio_cm"
    assert ultima.valor == 65.0
    # DataHora 09:15 hora do Rio = 12:15 UTC
    assert ultima.ts == datetime(2026, 8, 6, 12, 15, tzinfo=UTC)
    assert resultado.marca_frescor == ultima.ts


def test_as_4_estacoes_viram_locais_mesmo_sem_dado(fixtures: Path) -> None:
    xml = (fixtures / "ana_rio_tijuca.xml").read_bytes()
    resultado = _coletar_com({"59305071": xml})
    assert len(resultado.locais) == 4
    capela = next(loc for loc in resultado.locais if loc.codigo_externo == "59305071")
    assert capela.tipo == "estacao_rio"
    assert capela.lat == pytest.approx(-22.9568)


def test_estacao_muda_e_tolerada_mas_todas_mudas_nao(fixtures: Path) -> None:
    # Uma estação com dado + três "Sem dados" (o caso real de 06/08): coleta OK
    xml = (fixtures / "ana_rio_tijuca.xml").read_bytes()
    assert _coletar_com({"59305071": xml}).medicoes
    # Todas sem dado: fonte quebrada, tem que estourar
    with pytest.raises(ErroSchema):
        _coletar_com({})
