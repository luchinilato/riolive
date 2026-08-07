"""Parser de focos do INPE: listagem, CSV real e filtro espacial em duas etapas."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from riolive.fontes import queimadas_inpe
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp

LISTAGEM = b"""<html><body>
<a href="focos_10min_20260806_1240.csv">focos_10min_20260806_1240.csv</a>
<a href="focos_10min_20260806_1300.csv">focos_10min_20260806_1300.csv</a>
<a href="focos_10min_20260806_1250.csv">focos_10min_20260806_1250.csv</a>
<a href="focos_10min_20260806_1230.csv">focos_10min_20260806_1230.csv</a>
</body></html>"""

CSV_COM_FOCO_NO_RIO = (
    b"lat,lon,satelite,data\n"
    b" -22.958000, -43.278000,GOES-19,2026-08-06 12:50:00\n"  # Floresta da Tijuca
    b" -16.314600, -60.413000,GOES-19,2026-08-06 12:50:00\n"  # Bolívia: fora do bbox
)


def _coletar(csv_por_arquivo: dict[str, bytes]) -> queimadas_inpe.ResultadoColeta:
    with respx.mock:
        respx.get(queimadas_inpe.URL_LISTAGEM).mock(
            return_value=httpx.Response(200, content=LISTAGEM)
        )
        respx.get(url__regex=r".*focos_10min_\d{8}_\d{4}\.csv").mock(
            side_effect=lambda req: httpx.Response(
                200,
                content=csv_por_arquivo.get(
                    req.url.path.rsplit("/", 1)[-1], b"lat,lon,satelite,data\n"
                ),
            )
        )
        with ClienteHttp() as cliente:
            return queimadas_inpe.coletar(cliente)


def test_pega_os_3_arquivos_mais_recentes_da_listagem() -> None:
    resultado = _coletar({})
    # mais novo da listagem: 13:00 UTC — vira a marca de frescor mesmo sem foco algum
    assert resultado.marca_frescor == datetime(2026, 8, 6, 13, 0, tzinfo=UTC)
    assert resultado.eventos == []


def test_foco_fora_do_bbox_metropolitano_e_descartado_no_parser(fixtures: Path) -> None:
    # CSV real de 06/08: 10 focos, todos fora do RJ (Bolívia/MT) → zero eventos
    csv_real = (fixtures / "inpe_focos_10min.csv").read_bytes()
    resultado = _coletar({"focos_10min_20260806_1300.csv": csv_real})
    assert resultado.eventos == []


def test_foco_no_rio_vira_evento_pontual_com_filtro_de_bairro() -> None:
    resultado = _coletar({"focos_10min_20260806_1300.csv": CSV_COM_FOCO_NO_RIO})
    assert len(resultado.eventos) == 1
    foco = resultado.eventos[0]
    assert foco.tipo == "foco_calor"
    assert foco.severidade == 2
    assert foco.inicio == foco.fim == datetime(2026, 8, 6, 12, 50, tzinfo=UTC)
    assert foco.lat == pytest.approx(-22.958)
    assert foco.exigir_bairro  # etapa 2 do filtro: só grava se cair num bairro
    assert not foco.vigente


def test_listagem_vazia_e_falha_de_schema() -> None:
    with respx.mock:
        respx.get(queimadas_inpe.URL_LISTAGEM).mock(
            return_value=httpx.Response(200, content=b"<html>vazio</html>")
        )
        with ClienteHttp() as cliente, pytest.raises(ErroSchema):
            queimadas_inpe.coletar(cliente)
