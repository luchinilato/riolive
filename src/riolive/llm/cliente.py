"""Cliente de LLM via OpenRouter — a camada genérica, reusável por qualquer tarefa.

Um provedor só (OpenRouter) e modelo escolhido por chamada: trocar de modelo é
mudar uma string, e a tarefa não sabe quem está do outro lado.

Três decisões que a camada impõe a quem usa:

1. **Saída tipada ou nada.** Toda chamada declara um JSON Schema e o resultado é
   validado antes de voltar. Texto solto de LLM não entra no produto.
2. **Falha não derruba a tarefa.** Provedor fora, resposta inválida, cota
   estourada — tudo vira `ErroLlm`, e quem chama decide seguir sem o
   enriquecimento. LLM aqui é sempre acréscimo, nunca pré-requisito.
3. **Uso registrado.** Todo retorno traz tokens e custo em dólar, porque uma
   camada de IA sem contador vira surpresa na fatura.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from riolive.config import config

logger = logging.getLogger(__name__)

URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT = httpx.Timeout(120.0, connect=10.0)
TENTATIVAS = 3


class ErroLlm(Exception):
    """Qualquer falha da camada: rede, cota, resposta fora do schema."""


class _ErroTransitorio(Exception):
    """5xx ou 429 — interno ao ciclo de retry."""


@dataclass(frozen=True)
class Resposta:
    dados: dict[str, Any]  # já validado contra o schema pedido
    modelo: str  # o modelo que de fato respondeu (o roteador pode trocar)
    tokens_entrada: int
    tokens_saida: int
    custo_usd: float | None  # None quando o provedor não informa


@dataclass
class ClienteLlm:
    """Chamada tipada a um modelo. `modelo` sobrepõe o padrão da configuração."""

    modelo: str | None = None
    timeout: httpx.Timeout = field(default_factory=lambda: TIMEOUT)

    def __post_init__(self) -> None:
        cfg = config()
        self.modelo = self.modelo or cfg.llm_modelo
        chave = cfg.openrouter_api_key.get_secret_value()
        if not chave:
            # credencial ausente é defeito de configuração nosso, não falha de fonte
            raise RuntimeError("RIOLIVE_OPENROUTER_API_KEY ausente — configure o .env")
        self._cliente = httpx.Client(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {chave}",
                "Content-Type": "application/json",
                # OpenRouter usa estes dois na atribuição de uso; identificam o projeto
                "HTTP-Referer": "https://sinalcarioca.rio",
                "X-Title": "Sinal Carioca",
            },
        )

    @retry(
        stop=stop_after_attempt(TENTATIVAS),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((httpx.TransportError, _ErroTransitorio)),
        reraise=True,
    )
    def _pedir(self, corpo: dict[str, Any]) -> dict[str, Any]:
        resposta = self._cliente.post(URL, json=corpo)
        if resposta.status_code in (429, *range(500, 600)):
            raise _ErroTransitorio(f"HTTP {resposta.status_code} no OpenRouter")
        if resposta.status_code != 200:
            raise ErroLlm(f"HTTP {resposta.status_code}: {resposta.text[:300]}")
        return resposta.json()  # type: ignore[no-any-return]

    def extrair(
        self,
        *,
        instrucao: str,
        texto: str,
        schema: dict[str, Any],
        nome_schema: str = "extracao",
        temperatura: float = 0.0,
    ) -> Resposta:
        """Roda uma extração tipada. Levanta `ErroLlm` em qualquer falha.

        `temperatura` 0 por padrão: a mesma entrada deve render a mesma saída
        sempre que possível — o produto deduplica por chave natural, e variação
        entre coletas viraria evento duplicado.
        """
        corpo = {
            "model": self.modelo,
            "temperature": temperatura,
            "messages": [
                {"role": "system", "content": instrucao},
                {"role": "user", "content": texto},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": nome_schema, "strict": True, "schema": schema},
            },
        }
        try:
            bruto = self._pedir(corpo)
        except (httpx.TransportError, _ErroTransitorio) as exc:
            raise ErroLlm(f"OpenRouter inalcançável: {exc}") from exc

        if "error" in bruto:
            raise ErroLlm(f"OpenRouter recusou: {bruto['error']}")
        try:
            conteudo = bruto["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ErroLlm(f"resposta sem choices: {str(bruto)[:300]}") from exc
        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError as exc:
            # modelo que ignora o schema é modelo que não serve pra este uso
            raise ErroLlm(f"conteúdo não é JSON: {conteudo[:300]}") from exc
        if not isinstance(dados, dict):
            raise ErroLlm(f"esperava objeto JSON, veio {type(dados).__name__}")

        uso = bruto.get("usage") or {}
        return Resposta(
            dados=dados,
            modelo=bruto.get("model") or (self.modelo or ""),
            tokens_entrada=int(uso.get("prompt_tokens") or 0),
            tokens_saida=int(uso.get("completion_tokens") or 0),
            custo_usd=uso.get("cost"),
        )

    def fechar(self) -> None:
        self._cliente.close()
