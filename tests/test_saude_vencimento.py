"""Estado de fonte tem prazo de validade.

O incidente de 2026-08-07: a coleta parou por 6 h e a página seguiu anunciando
"20 de 21 fontes online". Não era bug de leitura — era o dado certo, velho, sem
nada dizendo que era velho. `saude_fonte` só ganha linha quando o estado MUDA,
então fonte saudável não produz registro, e o último "online" vale para sempre.
"""

from datetime import UTC, datetime, timedelta

from riolive.api.rotas.fontes import CADENCIAS_ATE_VENCER, VENCIMENTO_MINIMO_S, _vencido

AGORA = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)
CADENCIA_LENTA = 3600


def test_coleta_recente_nao_vence() -> None:
    ha_pouco = AGORA - timedelta(minutes=30)
    assert _vencido(CADENCIA_LENTA, ha_pouco, AGORA) == 0


def test_silencio_longo_vence_e_devolve_a_idade() -> None:
    """O retorno é a idade em segundos, não um booleano: a página precisa dizer
    HÁ QUANTO TEMPO, senão troca uma afirmação falsa por uma vaga."""
    parada = AGORA - timedelta(hours=6)
    assert _vencido(CADENCIA_LENTA, parada, AGORA) == 6 * 3600


def test_sem_noticia_nenhuma_vence() -> None:
    """`None` é o caso do incidente visto de fora: Redis reiniciado, carimbo
    perdido. Não sabemos — e é isso que tem que aparecer, não o último estado."""
    assert _vencido(CADENCIA_LENTA, None, AGORA) is None


def test_fonte_rapida_tem_piso_de_tolerancia() -> None:
    """Fonte de 1 min com 3 min de atraso é normal.

    Sem o piso, três cadências seriam 3 minutos e todo soluço de rede viraria
    'desconhecido' — o alarme perderia sentido por excesso.
    """
    atraso = timedelta(seconds=VENCIMENTO_MINIMO_S // 2)
    assert _vencido(60, AGORA - atraso, AGORA) == 0

    # Passado o piso, vence.
    passou = timedelta(seconds=VENCIMENTO_MINIMO_S + 60)
    assert _vencido(60, AGORA - passou, AGORA) == VENCIMENTO_MINIMO_S + 60


def test_cadencia_longa_manda_no_limite() -> None:
    """Fonte diária não pode vencer em 10 min só porque o piso existe."""
    diaria = 24 * 3600
    dois_dias = timedelta(days=2)
    assert _vencido(diaria, AGORA - dois_dias, AGORA) == 0
    assert CADENCIAS_ATE_VENCER * diaria > VENCIMENTO_MINIMO_S


def test_transicao_recente_conta_como_prova_de_coleta() -> None:
    """A assimetria é o ponto.

    Ausência de transição não prova nada — foi o que criou o incidente. Mas
    transição recente prova coleta recente, porque só se grava transição depois
    de coletar. Sem essa reserva, fonte de cadência diária apareceria como
    desconhecida por 24 h depois de cada deploy.
    """
    diaria = 24 * 3600
    transicionou = AGORA - timedelta(hours=1)
    assert _vencido(diaria, None, AGORA, transicionou) == 0

    # Reserva velha não salva nada: continua vencido.
    antiga = AGORA - timedelta(days=5)
    assert _vencido(diaria, None, AGORA, antiga) == 5 * 24 * 3600
