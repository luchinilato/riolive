"""Máquina de estados de saúde por fonte — lógica pura, sem I/O.

Três classes de falha, porque a reação é diferente (DEC - Monitoramento):
- rede: transitória; degrada primeiro, `fora` só após N falhas consecutivas.
- schema: nunca se resolve sozinha; `fora` (e alerta) na primeira ocorrência.
- frescor: responde e valida, mas o dado não muda há tempo anormal → `congelada`.
"""

from dataclasses import dataclass
from datetime import timedelta

LIMIAR_FALHAS_REDE = 3

# Estados que disparam alerta ao entrar (degradada não alerta: pode ser blip)
ESTADOS_ALERTA = frozenset({"fora", "congelada"})


@dataclass(frozen=True)
class Avaliacao:
    estado: str  # online | degradada | fora | congelada
    classe_falha: str | None  # rede | schema | frescor
    detalhe: str


def avaliar(
    classe_erro: str | None,
    falhas_rede_consecutivas: int,
    atraso_frescor: timedelta | None,
) -> Avaliacao:
    """Estado novo da fonte a partir do resultado de uma coleta.

    `classe_erro`: 'rede' ou 'schema' se a coleta falhou; None se teve sucesso.
    `falhas_rede_consecutivas`: contador já incluindo a falha atual.
    `atraso_frescor`: quanto o dado passou da tolerância; None = fresco ou sem marca.
    """
    if classe_erro == "schema":
        return Avaliacao("fora", "schema", "payload não bate com o schema esperado")
    if classe_erro == "rede":
        if falhas_rede_consecutivas >= LIMIAR_FALHAS_REDE:
            return Avaliacao(
                "fora", "rede", f"{falhas_rede_consecutivas} falhas de rede consecutivas"
            )
        return Avaliacao(
            "degradada", "rede", f"falha de rede ({falhas_rede_consecutivas}ª consecutiva)"
        )
    if atraso_frescor is not None:
        return Avaliacao(
            "congelada", "frescor", f"dado parado há {atraso_frescor} além da tolerância"
        )
    return Avaliacao("online", None, "coleta ok")


def deve_alertar(estado_anterior: str | None, avaliacao: Avaliacao) -> bool:
    """Alerta em transição pra estado grave e na recuperação a partir de um deles."""
    if avaliacao.estado == estado_anterior:
        return False
    if avaliacao.estado in ESTADOS_ALERTA:
        return True
    # recuperação: estava grave e voltou ao ar
    return avaliacao.estado == "online" and estado_anterior in ESTADOS_ALERTA
