"""Camada de LLM: cliente genérico e a extração dos comunicados do COR.

Nenhum teste chama o provedor — o cliente é dublado. O que se testa aqui é a
disciplina em volta do modelo: schema validado, coordenada implausível
descartada, falha isolada, e o `geom` do evento intocado.
"""

from typing import Any

import httpx
import pytest

from riolive.llm import interdicoes
from riolive.llm.cliente import ClienteLlm, ErroLlm, Resposta


class ClienteFalso:
    """Dublê do ClienteLlm: devolve o que o teste mandar, ou levanta."""

    def __init__(self, dados: dict[str, Any] | None = None, erro: Exception | None = None) -> None:
        self._dados = dados or {}
        self._erro = erro
        self.chamadas = 0

    def extrair(self, **_: Any) -> Resposta:
        self.chamadas += 1
        if self._erro:
            raise self._erro
        return Resposta(
            dados=self._dados,
            modelo="google/gemini-3.6-flash",
            tokens_entrada=800,
            tokens_saida=120,
            custo_usd=0.0007,
        )

    def fechar(self) -> None:
        pass


# ------------------------------------------------------------------ validações


def test_coordenada_fora_da_regiao_e_descartada() -> None:
    """A alucinação mais cara aqui é uma coordenada confiante e errada.

    O nome sobrevive — é mais do que tínhamos —, o ponto não.
    """
    brutos = [
        {"nome": "Elevado Paulo de Frontin", "tipo": "elevado", "lat": -22.92, "lon": -43.21},
        {"nome": "Avenida Paulista", "tipo": "via", "lat": -23.56, "lon": -46.65},  # São Paulo
    ]
    locais, descartados = interdicoes._locais_validos(brutos)
    assert descartados == 1
    assert locais[0]["lat"] == -22.92
    assert locais[1]["nome"] == "Avenida Paulista"
    assert locais[1]["lat"] is None, "fora da caixa: fica o nome, some o ponto"


def test_local_sem_nome_nao_entra() -> None:
    locais, _ = interdicoes._locais_validos(
        [{"nome": "  ", "tipo": "via", "lat": None, "lon": None}]
    )
    assert locais == []


def test_data_invalida_do_modelo_vira_nulo() -> None:
    # o modelo pode devolver "hoje às 22h" mesmo instruído a usar ISO
    assert interdicoes._instante("amanhã de manhã") is None
    assert interdicoes._instante(None) is None
    assert interdicoes._instante("2026-08-07T22:00:00-03:00") is not None


def test_esquema_e_estrito() -> None:
    """`strict` do provedor exige required completo e nada além do declarado."""
    assert interdicoes.ESQUEMA["additionalProperties"] is False
    assert set(interdicoes.ESQUEMA["required"]) == set(interdicoes.ESQUEMA["properties"])
    item = interdicoes.ESQUEMA["properties"]["locais"]["items"]
    assert item["additionalProperties"] is False
    assert set(item["required"]) == set(item["properties"])
    for campo in ("lat", "lon"):
        assert "null" in item["properties"][campo]["type"], "coordenada tem que poder faltar"


# ------------------------------------------------------------------ cliente


def _cliente_com(resposta: httpx.Response, monkeypatch: pytest.MonkeyPatch) -> ClienteLlm:
    monkeypatch.setenv("RIOLIVE_OPENROUTER_API_KEY", "chave-de-teste")
    from riolive.config import config

    config.cache_clear()
    cliente = ClienteLlm()
    monkeypatch.setattr(cliente._cliente, "post", lambda *a, **k: resposta)
    return cliente


def test_conteudo_fora_do_json_vira_erro(monkeypatch: pytest.MonkeyPatch) -> None:
    # modelo que ignora o schema não serve: melhor falhar que gravar lixo
    corpo = {"choices": [{"message": {"content": "não sou json"}}]}
    cliente = _cliente_com(httpx.Response(200, json=corpo), monkeypatch)
    with pytest.raises(ErroLlm):
        cliente.extrair(instrucao="i", texto="t", schema=interdicoes.ESQUEMA)


def test_erro_do_provedor_vira_erro_da_camada(monkeypatch: pytest.MonkeyPatch) -> None:
    corpo = {"error": {"message": "insufficient credits"}}
    cliente = _cliente_com(httpx.Response(200, json=corpo), monkeypatch)
    with pytest.raises(ErroLlm, match="recusou"):
        cliente.extrair(instrucao="i", texto="t", schema=interdicoes.ESQUEMA)


def test_uso_volta_junto_da_resposta(monkeypatch: pytest.MonkeyPatch) -> None:
    # camada de IA sem contador vira surpresa na fatura
    corpo = {
        "model": "google/gemini-3.6-flash",
        "choices": [
            {"message": {"content": '{"locais": [], "inicio": null, "fim": null, "resumo": "x"}'}}
        ],
        "usage": {"prompt_tokens": 812, "completion_tokens": 94, "cost": 0.0013},
    }
    cliente = _cliente_com(httpx.Response(200, json=corpo), monkeypatch)
    resposta = cliente.extrair(instrucao="i", texto="t", schema=interdicoes.ESQUEMA)
    assert resposta.tokens_entrada == 812
    assert resposta.custo_usd == 0.0013
    assert resposta.dados["resumo"] == "x"


def test_sem_chave_e_defeito_de_configuracao(monkeypatch: pytest.MonkeyPatch) -> None:
    """Credencial ausente é defeito nosso — estoura, não passa batido.

    O job checa antes e nem chega aqui; quem instancia o cliente na mão, sim.
    """
    monkeypatch.setenv("RIOLIVE_OPENROUTER_API_KEY", "")
    from riolive.config import config

    config.cache_clear()
    with pytest.raises(RuntimeError, match="OPENROUTER"):
        ClienteLlm()
    config.cache_clear()


# ------------------------------------------------------------------ tarefa


def test_sem_chave_a_extracao_e_pulada(monkeypatch: pytest.MonkeyPatch) -> None:
    # LLM é acréscimo: sem chave o produto segue igual, sem exceção
    monkeypatch.setenv("RIOLIVE_OPENROUTER_API_KEY", "")
    from riolive.config import config

    config.cache_clear()
    assert "pulado" in interdicoes.rodar()
    config.cache_clear()


def _banco_disponivel() -> bool:
    try:
        from sqlalchemy import text

        from riolive.db import sessao

        with sessao() as s:
            s.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _banco_disponivel(), reason="Postgres do compose fora do ar")
def test_extracao_grava_no_payload_e_nao_toca_na_geometria(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A extração é acréscimo lateral, nunca sobrescrita.

    Mexer no `geom` do evento quebraria a dedup (tipo, início, h3_r8): a próxima
    coleta do mesmo post não casaria com o que está gravado e entraria de novo.
    """
    from datetime import UTC, datetime

    from sqlalchemy import text

    from riolive.config import config
    from riolive.db import sessao

    monkeypatch.setenv("RIOLIVE_OPENROUTER_API_KEY", "chave-de-teste")
    config.cache_clear()

    inicio = datetime(2031, 1, 1, 12, 0, tzinfo=UTC)  # data absurda: não colide com dado real
    with sessao() as s:
        fonte_id = s.execute(text("SELECT id FROM fonte LIMIT 1")).scalar_one()
        s.execute(
            text(
                "INSERT INTO evento (tipo, fonte_id, severidade, inicio, fim, titulo, "
                "descricao, payload, coletado_em) VALUES ('interdicao', :f, 2, :i, :i, "
                "'Teste: interdição do Elevado Paulo de Frontin', 'Texto de teste.', "
                '\'{"link": "x"}\'::jsonb, now())'
            ),
            {"f": fonte_id, "i": inicio},
        )
        s.commit()

    falso = ClienteFalso(
        {
            "locais": [
                {
                    "nome": "Elevado Paulo de Frontin",
                    "tipo": "elevado",
                    "lat": -22.92,
                    "lon": -43.21,
                },
                {"nome": "Avenida Paulista", "tipo": "via", "lat": -23.56, "lon": -46.65},
            ],
            "inicio": "2031-01-01T22:00:00-03:00",
            "fim": None,
            "resumo": "Interdição para manutenção.",
        }
    )
    try:
        contadores = interdicoes.rodar(limite=50, cliente=falso)  # type: ignore[arg-type]
        assert contadores["processados"] >= 1
        assert contadores["pontos_descartados"] >= 1, "a coordenada de São Paulo tem que cair"

        with sessao() as s:
            linha = s.execute(
                text(
                    "SELECT payload, geom IS NULL AS sem_geom FROM evento "
                    "WHERE inicio = :i AND tipo = 'interdicao'"
                ),
                {"i": inicio},
            ).one()
        llm = linha.payload["llm"]
        assert linha.sem_geom, "o evento continua sem geometria própria"
        assert linha.payload["link"] == "x", "o payload da fonte é preservado"
        assert llm["locais"][0]["lat"] == -22.92
        assert llm["locais"][1]["lat"] is None
        assert llm["inicio"] is not None
        assert "não verificada" in llm["origem"]

        # idempotência: segunda rodada não re-processa o que já tem `llm`
        chamadas_antes = falso.chamadas
        interdicoes.rodar(limite=50, cliente=falso)  # type: ignore[arg-type]
        assert falso.chamadas == chamadas_antes, "evento já extraído não volta pro modelo"
    finally:
        with sessao() as s:
            s.execute(text("DELETE FROM evento WHERE inicio = :i"), {"i": inicio})
            s.commit()
        config.cache_clear()
