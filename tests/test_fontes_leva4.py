"""Leva final keyless: Diário Oficial e ISP-RJ."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from riolive.fontes import diario_oficial, isp_rj
from riolive.ingestao.contrato import ErroSchema
from riolive.ingestao.fetcher import ClienteHttp

EDICOES = (
    b'{"erro":false,"itens":[{"id":"14897","data":"06/08/2026","suplemento":0,'
    b'"numero":"97","paginas":"172"}]}'
)
PDF_FALSO = b"%PDF-1.7 conteudo"


def test_diario_oficial_vira_blob(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("RIOLIVE_R2_ENDPOINT", "")
    monkeypatch.setenv("RIOLIVE_BLOBS_DIR", str(tmp_path))
    from riolive.blobs import armazem
    from riolive.config import config

    config.cache_clear()
    armazem.cache_clear()
    with respx.mock:
        respx.get(url__startswith=diario_oficial.URL_EDICOES).mock(
            return_value=httpx.Response(200, content=EDICOES)
        )
        respx.get(url__regex=r".*/edicoes/download/\d+").mock(
            return_value=httpx.Response(200, content=PDF_FALSO)
        )
        with ClienteHttp() as cliente:
            resultado = diario_oficial.coletar(cliente)
    assert resultado.blobs
    blob = resultado.blobs[0]
    assert blob.caminho.startswith("diario_oficial/") and blob.caminho.endswith("_ed97.pdf")
    assert blob.meta is not None and blob.meta["paginas"] == "172"
    config.cache_clear()
    armazem.cache_clear()


def test_diario_oficial_nao_pdf_e_falha_de_schema(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setenv("RIOLIVE_R2_ENDPOINT", "")
    monkeypatch.setenv("RIOLIVE_BLOBS_DIR", str(tmp_path))
    from riolive.blobs import armazem
    from riolive.config import config

    config.cache_clear()
    armazem.cache_clear()
    with respx.mock:
        respx.get(url__startswith=diario_oficial.URL_EDICOES).mock(
            return_value=httpx.Response(200, content=EDICOES)
        )
        respx.get(url__regex=r".*/edicoes/download/\d+").mock(
            return_value=httpx.Response(200, content=b"<html>erro</html>")
        )
        with ClienteHttp() as cliente, pytest.raises(ErroSchema):
            diario_oficial.coletar(cliente)
    config.cache_clear()
    armazem.cache_clear()


CSV_ISP = "\n".join(
    [
        ";".join(
            [
                "cisp",
                "mes",
                "ano",
                "mes_ano",
                "aisp",
                "risp",
                "munic",
                "mcirc",
                "regiao",
                *isp_rj.METRICAS_ISP,
            ]
        ),
        "1;1;2023;2023m01;5;1;Rio de Janeiro;3304557;Capital;10;2;100;50;30;5",
        "4;1;2023;2023m01;5;1;Rio de Janeiro;3304557;Capital;5;1;80;20;25;3",
        "70;1;2023;2023m01;20;5;Niterói;3303302;Grande Niterói;99;9;99;99;99;9",
        "1;2;2023;2023m02;5;1;Rio de Janeiro;3304557;Capital;7;;60;10;;2",
    ]
).encode("latin-1")


def test_isp_soma_capital_por_mes() -> None:
    with respx.mock:
        respx.get(url__startswith=isp_rj.URL).mock(
            return_value=httpx.Response(200, content=CSV_ISP)
        )
        with ClienteHttp() as cliente:
            resultado = isp_rj.coletar(cliente)
    jan_letalidade = next(
        m
        for m in resultado.medicoes
        if m.metrica == "isp_letalidade_violenta" and m.ts == datetime(2023, 1, 1, tzinfo=UTC)
    )
    assert jan_letalidade.valor == 15  # 10 + 5; Niterói fora
    fev_hom = next(
        m
        for m in resultado.medicoes
        if m.metrica == "isp_hom_doloso" and m.ts == datetime(2023, 2, 1, tzinfo=UTC)
    )
    assert fev_hom.valor == 0  # campo vazio = 0
    assert resultado.locais[0].codigo_externo == "capital"
    assert resultado.marca_frescor == datetime(2023, 2, 1, tzinfo=UTC)


def test_isp_coluna_sumida_e_falha_de_schema() -> None:
    csv_quebrado = b"cisp;mes;ano;regiao\n1;1;2023;Capital"
    with respx.mock:
        respx.get(url__startswith=isp_rj.URL).mock(
            return_value=httpx.Response(200, content=csv_quebrado)
        )
        with ClienteHttp() as cliente, pytest.raises(ErroSchema):
            isp_rj.coletar(cliente)
