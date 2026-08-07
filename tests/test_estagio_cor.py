"""Parser do estágio operacional do COR sobre o JSON real capturado em 2026-08-06."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx
from pydantic import ValidationError

from riolive.fontes import estagio_cor
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp


def _coletar(conteudo: bytes) -> estagio_cor.ResultadoColeta:
    with respx.mock:
        respx.get(estagio_cor.URL).mock(return_value=httpx.Response(200, content=conteudo))
        with ClienteHttp() as cliente:
            return estagio_cor.coletar(cliente)


def test_payload_real_vira_evento_vigente(fixtures: Path) -> None:
    resultado = _coletar((fixtures / "estagio_cor.json").read_bytes())
    assert len(resultado.eventos) == 1
    evento = resultado.eventos[0]
    assert evento.tipo == "estagio_cor"
    assert evento.severidade == 1  # espelha literalmente o estágio
    assert evento.titulo == "Estágio 1"
    assert evento.vigente
    assert evento.fim is None
    assert evento.inicio == datetime(2026, 8, 5, 23, 0, 1, tzinfo=UTC)
    # cidade inteira: sem pino
    assert evento.lat is None and evento.lon is None


def test_estagio_fora_da_escala_e_rejeitado() -> None:
    corpo = (
        b'{"cor": "#000", "estagio": "Est\xc3\xa1gio 7", "id": 7, "inicio": "2026-08-05T23:00:01Z"}'
    )
    with pytest.raises(ValidationError):
        _coletar(corpo)


def test_id_divergente_do_texto_e_falha_de_schema() -> None:
    corpo = (
        b'{"cor": "#000", "estagio": "Est\xc3\xa1gio 2", "id": 3, "inicio": "2026-08-05T23:00:01Z"}'
    )
    with pytest.raises(ErroSchema):
        _coletar(corpo)


def test_resposta_nao_json_e_falha_de_schema() -> None:
    with pytest.raises(ErroSchema):
        _coletar(b"<html>fora do ar</html>")
