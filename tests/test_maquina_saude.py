"""Máquina de estados de saúde: 3 classes de falha, transições e política de alerta."""

from datetime import timedelta

from riolive.saude.maquina import LIMIAR_FALHAS_REDE, Avaliacao, avaliar, deve_alertar


def test_sucesso_fresco_fica_online() -> None:
    aval = avaliar(classe_erro=None, falhas_rede_consecutivas=0, atraso_frescor=None)
    assert aval.estado == "online"
    assert aval.classe_falha is None


def test_falha_de_rede_isolada_degrada_sem_derrubar() -> None:
    aval = avaliar(classe_erro="rede", falhas_rede_consecutivas=1, atraso_frescor=None)
    assert aval.estado == "degradada"
    assert aval.classe_falha == "rede"


def test_falhas_de_rede_consecutivas_derrubam() -> None:
    aval = avaliar(
        classe_erro="rede", falhas_rede_consecutivas=LIMIAR_FALHAS_REDE, atraso_frescor=None
    )
    assert aval.estado == "fora"
    assert aval.classe_falha == "rede"


def test_falha_de_schema_derruba_na_primeira() -> None:
    # "Mudou formato" nunca se resolve sozinho: fora imediato, sem carência
    aval = avaliar(classe_erro="schema", falhas_rede_consecutivas=0, atraso_frescor=None)
    assert aval.estado == "fora"
    assert aval.classe_falha == "schema"


def test_dado_parado_alem_da_tolerancia_congela() -> None:
    aval = avaliar(
        classe_erro=None, falhas_rede_consecutivas=0, atraso_frescor=timedelta(minutes=42)
    )
    assert aval.estado == "congelada"
    assert aval.classe_falha == "frescor"


def test_alerta_so_em_transicao_grave_e_recuperacao() -> None:
    fora = Avaliacao("fora", "rede", "")
    degradada = Avaliacao("degradada", "rede", "")
    online = Avaliacao("online", None, "")
    congelada = Avaliacao("congelada", "frescor", "")

    assert deve_alertar("online", fora)
    assert deve_alertar("online", congelada)
    assert deve_alertar("fora", online)  # recuperação
    assert not deve_alertar("online", degradada)  # pode ser blip: sem alerta
    assert not deve_alertar("fora", fora)  # sem transição, sem alerta
    assert not deve_alertar("degradada", online)  # recuperar de degradada não alerta
