"""Estado operacional da máquina de saúde entre execuções (Redis).

Runs do Dagster são processos separados: contador de falhas consecutivas, último
estado conhecido e cooldown de alertas precisam sobreviver ao processo. Se o Redis
estiver fora, degrada pra memória do processo — ingestão nunca para por causa dele.
"""

import logging
from datetime import datetime

import redis

from riolive.config import config

logger = logging.getLogger(__name__)

_memoria: dict[str, str] = {}  # fallback se o Redis estiver indisponível

# 7 dias cobre a fonte mais lenta com folga; passou disso, "sem notícia" é a
# resposta honesta, e é a que queremos que apareça.
TTL_COLETA_S = 7 * 24 * 3600


class ControleSaude:
    def __init__(self, slug: str, cliente: redis.Redis | None = None) -> None:
        self._slug = slug
        self._redis = cliente if cliente is not None else redis.Redis.from_url(config().redis_url)

    def _chave(self, sufixo: str) -> str:
        return f"riolive:saude:{self._slug}:{sufixo}"

    def registrar_falha_rede(self) -> int:
        """Incrementa e retorna o total de falhas de rede consecutivas."""
        try:
            return int(self._redis.incr(self._chave("falhas_rede")))
        except redis.RedisError:
            logger.warning("Redis indisponível; contando falhas em memória")
            total = int(_memoria.get(self._chave("falhas_rede"), "0")) + 1
            _memoria[self._chave("falhas_rede")] = str(total)
            return total

    def zerar_falhas_rede(self) -> None:
        try:
            self._redis.delete(self._chave("falhas_rede"))
        except redis.RedisError:
            _memoria.pop(self._chave("falhas_rede"), None)

    def estado_anterior(self) -> str | None:
        try:
            valor = self._redis.get(self._chave("estado"))
            return valor.decode() if isinstance(valor, bytes) else valor
        except redis.RedisError:
            return _memoria.get(self._chave("estado"))

    def gravar_estado(self, estado: str) -> None:
        try:
            self._redis.set(self._chave("estado"), estado)
        except redis.RedisError:
            _memoria[self._chave("estado")] = estado

    def marcar_coleta(self, quando: datetime) -> None:
        """Carimba que esta fonte foi coletada agora — deu certo ou não.

        `saude_fonte` só ganha linha quando o estado MUDA, então fonte saudável
        há dias não produz registro nenhum. Sem este carimbo não há como
        distinguir "online e coletando" de "online era o último estado antes de
        tudo parar" — e foi essa indistinção que fez a status page anunciar 20
        de 21 fontes no ar com o pipeline morto havia 6 h.

        O TTL é o que dá a resposta certa de graça: expirado, a chave some e a
        fonte aparece como desconhecida em vez de eternamente no último estado.
        """
        try:
            self._redis.set(self._chave("ultima_coleta"), quando.isoformat(), ex=TTL_COLETA_S)
        except redis.RedisError:
            _memoria[self._chave("ultima_coleta")] = quando.isoformat()

    def ultima_coleta(self) -> datetime | None:
        """Quando esta fonte foi coletada pela última vez, ou None se sem notícia."""
        try:
            valor = self._redis.get(self._chave("ultima_coleta"))
        except redis.RedisError:
            valor = _memoria.get(self._chave("ultima_coleta"))
        if valor is None:
            return None
        texto = valor.decode() if isinstance(valor, bytes) else str(valor)
        try:
            return datetime.fromisoformat(texto)
        except ValueError:
            return None

    def tentar_iniciar_cooldown(self) -> bool:
        """True se não havia cooldown ativo (pode alertar); inicia a janela.

        Primeiro alerta é imediato; repetições dentro da janela são silenciadas.
        """
        segundos = config().alerta_cooldown_min * 60
        try:
            return bool(self._redis.set(self._chave("cooldown"), "1", nx=True, ex=segundos))
        except redis.RedisError:
            # Sem Redis não há janela confiável entre processos: melhor alertar demais
            # que silenciar um incidente real.
            return True
