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


def _yaml(caminho: str) -> dict:
    import yaml

    return yaml.safe_load((RAIZ / caminho).read_text())


def test_codigo_carrega_de_servidor_dedicado_e_nao_de_modulo() -> None:
    """`python_module` no workspace é o que fabrica run zumbi.

    Com ele, webserver e daemon sobem cada um um code server efêmero com
    heartbeat; o servidor que perde o heartbeat se desliga e leva junto os runs
    que executavam dentro dele, que ficam STARTED para sempre e entopem a fila
    de 10. Derrubou a coleta em 2026-08-07 (6 h) e de novo em 2026-08-08 (38
    min). Servidor dedicado não tem heartbeat para perder — e, quando reinicia,
    o `run_monitoring` consegue enterrar os runs porque tem a quem perguntar.
    """
    carga = _yaml("workspace.yaml")["load_from"]
    assert len(carga) == 1, carga
    entrada = carga[0]
    assert "python_module" not in entrada, "voltou o code server efêmero: " + str(entrada)
    assert "grpc_server" in entrada, entrada


def test_servidor_de_codigo_existe_no_compose_com_a_mesma_porta() -> None:
    """Host e porta do workspace têm que casar com o serviço, senão nada carrega.

    Errar aqui não dá erro de sintaxe em lugar nenhum: o daemon sobe, a UI
    mostra a location em falha e nenhuma coleta acontece.
    """
    alvo = _yaml("workspace.yaml")["load_from"][0]["grpc_server"]
    servicos = _yaml("docker-compose.yml")["services"]

    assert alvo["host"] in servicos, f"{alvo['host']} não é serviço do compose"
    comando = servicos[alvo["host"]]["command"]
    assert "dagster api grpc" in comando, comando
    assert f"-p {alvo['port']}" in comando, (comando, alvo["port"])
    # O módulo do comando é o que o Dagster vai importar: errado, sobe vazio.
    assert "-m riolive.orquestracao.definitions" in comando, comando

    for dependente in ("dagster-daemon", "dagster-webserver"):
        assert alvo["host"] in servicos[dependente]["depends_on"], dependente


@pytest.mark.parametrize("caminho", CONFIGS)
def test_teto_de_simultaneidade_abaixo_do_padrao(caminho: str) -> None:
    """Dez runs simultâneos saturaram a máquina e o resto veio em cascata.

    Máquina saturada → code server sem heartbeat → run zumbi → fila cheia → ao
    drenar, satura de novo. O teto é o que quebra o ciclo, e voltar ao padrão
    tem que ser decisão de alguém, não o efeito de apagar um bloco do YAML.
    """
    with tempfile.TemporaryDirectory() as dir_tmp:
        shutil.copy(RAIZ / caminho, Path(dir_tmp) / "dagster.yaml")
        config, _ = dagster_instance_config(dir_tmp)
    teto = config["run_coordinator"]["config"]["max_concurrent_runs"]
    assert 0 < teto <= 5, teto
