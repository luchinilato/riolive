"""Armazém de blobs: backend local e seleção por configuração."""

from pathlib import Path

import pytest

from riolive.blobs import ArmazemLocal, ArmazemR2, armazem
from riolive.config import config


def test_armazem_local_grava_e_confere(tmp_path: Path) -> None:
    deposito = ArmazemLocal(str(tmp_path))
    caminho = deposito.salvar("radar/2026/08/x.png", b"\x89PNG teste")
    assert caminho == "radar/2026/08/x.png"
    assert deposito.existe(caminho)
    assert not deposito.existe("radar/nao-existe.png")
    assert (tmp_path / caminho).read_bytes() == b"\x89PNG teste"


def test_factory_escolhe_pelo_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    def limpar() -> None:
        config.cache_clear()
        armazem.cache_clear()

    monkeypatch.setenv("RIOLIVE_R2_ENDPOINT", "")
    limpar()
    assert isinstance(armazem(), ArmazemLocal)

    monkeypatch.setenv("RIOLIVE_R2_ENDPOINT", "https://exemplo.r2.cloudflarestorage.com")
    monkeypatch.setenv("RIOLIVE_R2_ACCESS_KEY_ID", "chave")
    monkeypatch.setenv("RIOLIVE_R2_SECRET_ACCESS_KEY", "segredo")
    monkeypatch.setenv("RIOLIVE_R2_BUCKET", "balde")
    limpar()
    assert isinstance(armazem(), ArmazemR2)
    limpar()
