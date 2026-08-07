"""Feed do COR e avisos do INMET, contra as fixtures capturadas em 2026-08-07."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from riolive.fontes import cor_feed, inmet_avisos
from riolive.ingestao.contrato import ErroSchema

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def xml_cor() -> str:
    return (FIXTURES / "cor_feed.xml").read_text(encoding="utf-8")


@pytest.fixture
def xml_inmet() -> str:
    return (FIXTURES / "inmet_avisos_rss.xml").read_text(encoding="utf-8")


# ------------------------------------------------------------------ COR


def test_cor_le_os_dez_itens_do_feed(xml_cor: str) -> None:
    resultado = cor_feed.interpretar(xml_cor)
    assert len(resultado.eventos) == 10
    assert resultado.marca_frescor is not None


def test_cor_classifica_pela_categoria_do_publicador(xml_cor: str) -> None:
    # a classificação não é heurística de título: o feed traz <category>
    eventos = cor_feed.interpretar(xml_cor).eventos
    interdicoes = [e for e in eventos if e.tipo == "interdicao"]
    # duas manutenções de túneis/elevados + as duas de jogo (Maracanã e Engenhão)
    assert len(interdicoes) == 4
    assert all("Interdições" in (e.payload or {})["categorias"] for e in interdicoes)
    assert all(e.severidade == 2 for e in interdicoes)


def test_cor_guarda_o_link_do_post(xml_cor: str) -> None:
    # comunicado é texto, não medição: o leitor tem que poder ir na fonte
    eventos = cor_feed.interpretar(xml_cor).eventos
    assert all((e.payload or {}).get("link", "").startswith("https://cor.rio/") for e in eventos)


def test_cor_traz_o_motivo_do_estagio(xml_cor: str) -> None:
    # o número do estágio vem da fonte `estagio_cor`; aqui está o porquê
    titulos = " | ".join(e.titulo for e in cor_feed.interpretar(xml_cor).eventos)
    assert "Estágio 3" in titulos
    assert "ventos" in titulos.lower()


def test_cor_sem_item_e_erro_de_schema() -> None:
    with pytest.raises(ErroSchema):
        cor_feed.interpretar("<rss><channel></channel></rss>")


# ------------------------------------------------------------------ INMET


def test_inmet_filtra_a_regiao_metropolitana(xml_inmet: str) -> None:
    eventos = inmet_avisos.interpretar(xml_inmet).eventos
    # 99 avisos no feed (América do Sul); só os da área do Rio entram
    assert 0 < len(eventos) < 30
    assert all("metropolitana" in (e.payload or {})["area"].lower() for e in eventos)


def test_inmet_mapeia_o_grau_de_perigo(xml_inmet: str) -> None:
    eventos = inmet_avisos.interpretar(xml_inmet).eventos
    graus = {(e.payload or {})["grau"]: e.severidade for e in eventos}
    assert graus, "esperava ao menos um aviso na área do Rio"
    for grau, severidade in graus.items():
        assert severidade == inmet_avisos.SEVERIDADE[grau.lower()]
        assert 2 <= severidade <= 4


def test_inmet_tipa_cada_fenomeno_separado(xml_inmet: str) -> None:
    """Dedup de evento pontual é (tipo, início, h3). Sem tipo por fenômeno, três
    avisos diferentes que começam à meia-noite viram um só no banco."""
    eventos = inmet_avisos.interpretar(xml_inmet).eventos
    chaves = {(e.tipo, e.inicio) for e in eventos}
    assert len(chaves) == len(eventos), "dois avisos colidiriam na chave natural"
    unidos = [e for e in eventos if (e.payload or {}).get("avisos_unidos", 1) > 1]
    assert unidos, "a fixture tem reemissão do INMET (Tempestade e Vendaval)"
    for e in unidos:
        assert e.fim is not None  # a união fica com a validade mais longa
    assert all(e.tipo.startswith("aviso_") for e in eventos)


def test_inmet_le_o_horario_como_hora_de_brasilia(xml_inmet: str) -> None:
    """Janela de dia inteiro fecha em 00:00–23:59 local — se fosse lida como UTC,
    o aviso apareceria começando às 21h do dia anterior."""
    eventos = inmet_avisos.interpretar(xml_inmet).eventos
    dia_inteiro = [e for e in eventos if e.fim and (e.fim - e.inicio).seconds >= 86340 - 1]
    assert dia_inteiro, "a fixture tem avisos de dia inteiro"
    for e in dia_inteiro:
        # 00:00 em Brasília (UTC-3) é 03:00 em UTC
        assert e.inicio.astimezone(UTC).hour == 3


def test_inmet_titulo_diz_que_o_aviso_e_regional(xml_inmet: str) -> None:
    # o feed não tem IBGE: prometer recorte municipal seria afirmar o que não temos
    eventos = inmet_avisos.interpretar(xml_inmet).eventos
    assert all("região metropolitana" in e.titulo for e in eventos)


def test_inmet_grau_desconhecido_derruba_a_fonte(xml_inmet: str) -> None:
    """Escala nova na origem estoura em vez de virar severidade errada em silêncio.

    Mas só quando atinge aviso que consumimos: grau esquisito numa área fora do
    Rio não invalida o nosso dado, e derrubar a fonte por isso repetiria o erro
    que deixou o `estagio_cor` um dia fora do ar.
    """
    marcado = xml_inmet.replace(
        '<th align="left">Severidade</th><td>Perigo</td>',
        '<th align="left">Severidade</th><td>Perigo Cósmico</td>',
    )
    with pytest.raises(ErroSchema):
        inmet_avisos.interpretar(marcado)


def _item(evento: str, grau: str, area: str) -> str:
    return (
        "<item><description><![CDATA[<table>"
        f"<tr><th align='left'>Status</th><td>Alert</td></tr>"
        f"<tr><th align='left'>Evento</th><td>{evento}</td></tr>"
        f"<tr><th align='left'>Severidade</th><td>{grau}</td></tr>"
        "<tr><th align='left'>Início</th><td>2026-08-07 00:00:00.0</td></tr>"
        "<tr><th align='left'>Fim</th><td>2026-08-07 23:59:00.0</td></tr>"
        f"<tr><th align='left'>Área</th><td>Aviso para as Áreas: {area}</td></tr>"
        "</table>]]></description></item>"
    )


def test_inmet_grau_esquisito_fora_do_rio_nao_derruba() -> None:
    """O crosscheck é sobre o dado que a gente usa, não sobre o feed inteiro.

    Grau desconhecido num aviso do Rio Grande do Sul não invalida nada nosso;
    derrubar a fonte por isso repetiria o erro que deixou o `estagio_cor` um dia
    fora do ar. [[DEC - Crosscheck de fonte só reprova o que invalida o dado]]
    """
    xml = (
        "<rss><channel><pubDate>Fri, 07 Aug 2026 18:10:36 +0000</pubDate>"
        + _item("Tempestade", "Perigo Cósmico", "Sudoeste Rio-grandense")
        + _item("Vendaval", "Perigo", "Metropolitana do Rio de Janeiro")
        + "</channel></rss>"
    )
    eventos = inmet_avisos.interpretar(xml).eventos
    assert len(eventos) == 1
    assert eventos[0].tipo == "aviso_vendaval"


def test_inmet_formato_diferente_e_erro_de_schema() -> None:
    with pytest.raises(ErroSchema):
        inmet_avisos.interpretar(
            "<rss><channel><item><description>oi</description></item></channel></rss>"
        )


def test_inmet_marca_frescor_vem_do_canal(xml_inmet: str) -> None:
    # dia sem aviso pro Rio é normal; o frescor mede o feed, não o movimento
    resultado = inmet_avisos.interpretar(xml_inmet)
    assert resultado.marca_frescor == datetime(2026, 8, 7, 18, 10, 36, tzinfo=UTC)


def test_403_e_falha_transitoria_nao_de_schema() -> None:
    """Cloudflare barrando não é "a origem mudou de formato".

    Em 2026-08-07 o `cor.rio` alternou entre 200 e 403 para o mesmo cliente em
    minutos, por reputação de IP. Classificar isso como `schema` marca a fonte
    com a classe errada na página de status e alerta o time por nada.
    """
    from riolive.fontes.comum import erro_de_status
    from riolive.ingestao.fetcher import ErroRede

    for status in (403, 429):
        assert isinstance(erro_de_status(status, "x"), ErroRede)
    for status in (400, 404, 418):
        assert isinstance(erro_de_status(status, "x"), ErroSchema)
