"""Configurações do riolive, lidas do ambiente (prefixo RIOLIVE_) e do .env."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RIOLIVE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://riolive:riolive@localhost:5432/riolive"
    redis_url: str = "redis://localhost:6379/0"

    # Identificação do coletor: entra no User-Agent de toda requisição
    contato: str = "luciano@rheunion.com"

    # Alertas por e-mail (sem smtp_host, alertas são apenas logados)
    smtp_host: str = ""
    smtp_porta: int = 587
    smtp_usuario: str = ""
    smtp_senha: SecretStr = SecretStr("")
    alerta_email_destino: str = ""
    alerta_cooldown_min: int = 30

    # Dead-man's switch (healthchecks.io); vazio desativa
    healthchecks_url: str = ""

    # Sentry; vazio desativa
    sentry_dsn: str = ""

    # Blobs (radar, PDFs): disco local em dev; R2 em produção quando configurado
    blobs_dir: str = "dados/blobs"

    # Chaves de fontes (fase 1+)
    openaq_api_key: SecretStr = SecretStr("")
    tomtom_api_key: SecretStr = SecretStr("")
    aisstream_api_key: SecretStr = SecretStr("")

    @property
    def user_agent(self) -> str:
        return f"riolive/0.1 (coletor de dados abertos; contato: {self.contato})"


@lru_cache
def config() -> Config:
    return Config()
