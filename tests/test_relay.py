"""Desvio pelo relay: só o host declarado sai por lá.

O risco que estes testes cobrem não é o relay falhar — é o relay funcionar
demais. Se todo host passar a sair por um ponto único, um bloqueio conhecido em
uma fonte vira uma dependência capaz de derrubar todas de uma vez.
"""

from riolive.config import Config
from riolive.ingestao.fetcher import ClienteHttp

RELAY = "https://relay.exemplo.workers.dev"
ALVO = "https://api.ondeestameutrem.metrorio.app/v1/StatusLinha"
TOKEN_FALSO = "segredo-de-teste"  # noqa: S105
OUTRO = "https://apidadosabertos.rio.gov.br/qualquer"


def _com_config(monkeypatch, **campos: str) -> None:
    from riolive.ingestao import fetcher

    monkeypatch.setattr(fetcher, "config", lambda: Config(**campos))


def test_host_declarado_sai_pelo_relay(monkeypatch) -> None:
    _com_config(
        monkeypatch,
        proxy_saida=RELAY,
        proxy_hosts="api.ondeestameutrem.metrorio.app",
        proxy_token=TOKEN_FALSO,
    )
    url, headers = ClienteHttp()._desviar(ALVO, {"Authorization": "Bearer x"})

    assert url == RELAY
    assert headers is not None
    # A URL real viaja em header: o Worker valida o host antes de sair.
    assert headers["X-Riolive-Alvo"] == ALVO
    assert headers["X-Riolive-Token"] == TOKEN_FALSO
    # Header da fonte tem que sobreviver ao desvio, senão o metrô perde o Bearer.
    assert headers["Authorization"] == "Bearer x"


def test_host_nao_declarado_vai_direto(monkeypatch) -> None:
    _com_config(monkeypatch, proxy_saida=RELAY, proxy_hosts="api.ondeestameutrem.metrorio.app")
    assert ClienteHttp()._desviar(OUTRO, None) == (OUTRO, None)


def test_sem_relay_configurado_nada_desvia(monkeypatch) -> None:
    """Ausência de config é o padrão em dev e no CI — e tem que ser inerte."""
    _com_config(monkeypatch, proxy_hosts="api.ondeestameutrem.metrorio.app")
    assert ClienteHttp()._desviar(ALVO, None) == (ALVO, None)
