"""Parser do GPS BRT sobre payload real capturado em 2026-08-06."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from riolive.fontes import gps_brt
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp


def _coletar(conteudo: bytes) -> gps_brt.ResultadoColeta:
    with respx.mock:
        respx.get(gps_brt.URL).mock(return_value=httpx.Response(200, content=conteudo))
        with ClienteHttp() as cliente:
            return gps_brt.coletar(cliente)


def test_payload_real_vira_posicoes(fixtures: Path) -> None:
    resultado = _coletar((fixtures / "gps_brt.json").read_bytes())
    assert len(resultado.posicoes) == 200
    assert {p.modal for p in resultado.posicoes} == {"brt"}
    assert resultado.marca_frescor == max(p.ts for p in resultado.posicoes)


def test_campos_ricos_vao_pro_extra(fixtures: Path) -> None:
    resultado = _coletar((fixtures / "gps_brt.json").read_bytes())
    # veículo 901008 da fixture: epoch 1786021190000, vel 11.9, sentido ida
    veiculo = next(p for p in resultado.posicoes if p.veiculo_id == "901008")
    assert veiculo.ts == datetime.fromtimestamp(1786021190, tz=UTC)
    assert veiculo.velocidade == 12  # 11.9 arredondado pro smallint
    assert veiculo.linha == "22"
    assert veiculo.extra is not None and veiculo.extra["sentido"] == "ida"


def test_payload_sem_lista_veiculos_e_falha_de_schema() -> None:
    with pytest.raises(ErroSchema):
        _coletar(b'{"erro": "manutencao"}')
