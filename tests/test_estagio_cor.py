"""Parser do estágio operacional do COR sobre o JSON real capturado em 2026-08-06."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

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
    with pytest.raises(ErroSchema):
        _coletar(corpo)


def test_id_divergente_nao_derruba_a_fonte() -> None:
    """Payload real de 2026-08-06: id=1 com texto "Estágio 2" e cor amarela.

    O crosscheck antigo exigia id == texto e deixou a fonte de criticidade 5 fora
    do ar por um dia recusando dado bom. Quem manda é o texto.
    """
    corpo = (
        b'{"cor": "#f2c94c", "estagio": "Est\xc3\xa1gio 2", "mensagem": "", "id": 1,'
        b' "inicio": "2026-08-06T22:08:57Z"}'
    )
    resultado = _coletar(corpo)
    evento = resultado.eventos[0]
    assert evento.severidade == 2
    assert evento.titulo == "Estágio 2"
    assert evento.payload is not None and evento.payload["id"] == 1  # metadado, não some


def test_cor_divergente_tambem_nao_derruba() -> None:
    # Cor verde (estágio 1) com texto dizendo 3: loga e segue pelo texto
    corpo = (
        b'{"cor": "#228d46", "estagio": "Est\xc3\xa1gio 3", "id": 9,'
        b' "inicio": "2026-08-05T23:00:01Z"}'
    )
    resultado = _coletar(corpo)
    assert resultado.eventos[0].severidade == 3


def test_texto_sem_numero_e_falha_de_schema() -> None:
    corpo = b'{"cor": "#000", "estagio": "Normalidade", "id": 1, "inicio": "2026-08-05T23:00:01Z"}'
    with pytest.raises(ErroSchema):
        _coletar(corpo)


def test_resposta_nao_json_e_falha_de_schema() -> None:
    with pytest.raises(ErroSchema):
        _coletar(b"<html>fora do ar</html>")
