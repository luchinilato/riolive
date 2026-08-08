"""As configs do Dagster passam pelo schema oficial antes de virarem deploy.

Chave errada em `dagster.yaml` não é aviso: o daemon **não sobe**, entra em
crashloop e a coleta para. Aconteceu em 2026-08-07 com `max_resume_attempts`
no lugar de `max_resume_run_attempts` — um caractere de diferença, produção
parada, e o gate inteiro (ruff, mypy, 133 testes) passou verde, porque nada
olhava esse arquivo.
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from dagster._core.instance.config import dagster_instance_config

CONFIGS = ("docker/dagster.yaml", "deploy/dagster.prod.yaml")
RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("caminho", CONFIGS)
def test_config_valida_no_schema_do_dagster(caminho: str) -> None:
    """`dagster_instance_config` levanta se houver chave desconhecida."""
    origem = RAIZ / caminho
    assert origem.exists(), caminho
    with tempfile.TemporaryDirectory() as dir_tmp:
        shutil.copy(origem, Path(dir_tmp) / "dagster.yaml")
        config, _ = dagster_instance_config(dir_tmp)
    assert "storage" in config


@pytest.mark.parametrize("caminho", CONFIGS)
def test_run_monitoring_ligado(caminho: str) -> None:
    """Sem ele, todo deploy deixa runs zumbis que ocupam a fila até travá-la.

    O teste existe para que remover a chave seja uma decisão, não um descuido.
    """
    with tempfile.TemporaryDirectory() as dir_tmp:
        shutil.copy(RAIZ / caminho, Path(dir_tmp) / "dagster.yaml")
        config, _ = dagster_instance_config(dir_tmp)
    assert config.get("run_monitoring", {}).get("enabled") is True
