"""Registro de saúde do detector de linha parada.

O detector aparece na página pública de status como qualquer fonte. Antes de
2026-08-07 ele nunca gravava transição e ficava `desconhecido` pra sempre —
inclusive rodando bem. Estes testes cobrem a regra de gravação, sem tocar no
banco: o que importa é gravar na mudança e calar na repetição.
"""

from datetime import UTC, datetime
from typing import Any

import pytest

from riolive.detectores import linha_parada


class _SessaoFalsa:
    def __init__(self) -> None:
        self.adicionados: list[Any] = []

    def add(self, obj: Any) -> None:
        self.adicionados.append(obj)


class _ControleFalso:
    """Dublê do ControleSaude — o de verdade fala com o Redis."""

    def __init__(self, estado: str | None) -> None:
        self._estado = estado
        self.gravados: list[str] = []

    def estado_anterior(self) -> str | None:
        return self._estado

    def gravar_estado(self, estado: str) -> None:
        self._estado = estado
        self.gravados.append(estado)


@pytest.fixture
def agora() -> datetime:
    return datetime(2026, 8, 7, 6, 0, tzinfo=UTC)


def _rodar(monkeypatch: pytest.MonkeyPatch, anterior: str | None) -> tuple[Any, Any]:
    controle = _ControleFalso(anterior)
    monkeypatch.setattr(linha_parada, "ControleSaude", lambda _slug: controle)
    return _SessaoFalsa(), controle


def test_mudanca_de_estado_grava_transicao(
    monkeypatch: pytest.MonkeyPatch, agora: datetime
) -> None:
    s, controle = _rodar(monkeypatch, anterior=None)
    linha_parada._registrar_saude(s, 1, agora, "degradada", "em espera: GPS fora")
    assert controle.gravados == ["degradada"]
    assert len(s.adicionados) == 1
    linha = s.adicionados[0]
    assert linha.estado == "degradada"
    assert linha.detalhe == "em espera: GPS fora"
    # espera por dependência não é rede, schema nem frescor — e sem classe evita migration
    assert linha.classe_falha is None


def test_estado_repetido_nao_grava_de_novo(
    monkeypatch: pytest.MonkeyPatch, agora: datetime
) -> None:
    s, controle = _rodar(monkeypatch, anterior="degradada")
    linha_parada._registrar_saude(s, 1, agora, "degradada", "em espera: GPS fora")
    assert controle.gravados == []
    assert s.adicionados == []


def test_volta_pra_online_grava(monkeypatch: pytest.MonkeyPatch, agora: datetime) -> None:
    s, controle = _rodar(monkeypatch, anterior="degradada")
    linha_parada._registrar_saude(s, 1, agora, "online", "89 linhas planejadas agora")
    assert controle.gravados == ["online"]
    assert s.adicionados[0].estado == "online"
