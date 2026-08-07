"""Camada de LLM do riolive.

`cliente.py` é genérico e serve qualquer tarefa; cada uso vive no seu próprio
módulo (`interdicoes.py` é o primeiro). Regra que vale pra todos:

> Evento extraído de texto é **relato, não medição**. Nunca alimenta número de
> cartão, índice ou painel de segurança, e sai sempre rotulado com a origem e
> com "não verificado". A extração é acréscimo: se o LLM falhar, o evento
> continua existindo com o que a fonte publicou.

Decidido no vault (bloco "Camada extração de eventos por LLM") e reafirmado ao
integrar o feed do COR em 2026-08-07.
"""

from riolive.llm.cliente import ClienteLlm, ErroLlm, Resposta

__all__ = ["ClienteLlm", "ErroLlm", "Resposta"]
