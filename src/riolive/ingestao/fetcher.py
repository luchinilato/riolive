"""Cliente HTTP genérico dos coletores: httpx + tenacity.

Toda requisição sai com user-agent identificado, timeout e retry com backoff
exponencial. Falha de rede (timeout, conexão, 5xx persistente) vira ErroRede —
a classe de falha transitória da máquina de estados de saúde.
"""

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from riolive.config import config

TIMEOUT_PADRAO = httpx.Timeout(30.0, connect=10.0)
TENTATIVAS = 3


class ErroRede(Exception):
    """Fonte inalcançável: timeout, erro de conexão ou 5xx após os retries."""


class _ErroServidor(Exception):
    """5xx individual, interno ao ciclo de retry."""


class ClienteHttp:
    def __init__(self, timeout: httpx.Timeout = TIMEOUT_PADRAO) -> None:
        self._cliente = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": config().user_agent},
            follow_redirects=True,
        )

    @retry(
        stop=stop_after_attempt(TENTATIVAS),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        retry=retry_if_exception_type((httpx.TransportError, _ErroServidor)),
        reraise=True,
    )
    def _obter_com_retry(
        self, url: str, params: dict[str, str] | None, headers: dict[str, str] | None
    ) -> httpx.Response:
        resposta = self._cliente.get(url, params=params, headers=headers)
        if resposta.status_code >= 500:
            raise _ErroServidor(f"HTTP {resposta.status_code} em {url}")
        return resposta

    def obter(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """GET com retry. Levanta ErroRede se a fonte estiver inalcançável.

        4xx NÃO é erro de rede: retorna a resposta pro parser decidir
        (contrato quebrado costuma ser classe `schema`, não `rede`).
        `headers` extras (ex. X-API-Key) somam aos padrão do cliente.
        """
        try:
            return self._obter_com_retry(url, params, headers)
        except (httpx.TransportError, _ErroServidor) as exc:
            raise ErroRede(str(exc)) from exc

    def fechar(self) -> None:
        self._cliente.close()

    def __enter__(self) -> "ClienteHttp":
        return self

    def __exit__(self, *exc: object) -> None:
        self.fechar()
