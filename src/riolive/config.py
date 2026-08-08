"""Configurações do riolive, lidas do ambiente (prefixo RIOLIVE_) e do .env."""

from functools import lru_cache

from pydantic import Field, SecretStr
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

    # Blobs (radar, PDFs): R2 quando configurado; senão disco local (dev)
    blobs_dir: str = "dados/blobs"
    r2_endpoint: str = ""
    r2_access_key_id: SecretStr = SecretStr("")
    r2_secret_access_key: SecretStr = SecretStr("")
    r2_bucket: str = ""

    @property
    def r2_configurado(self) -> bool:
        return bool(
            self.r2_endpoint
            and self.r2_bucket
            and self.r2_access_key_id.get_secret_value()
            and self.r2_secret_access_key.get_secret_value()
        )

    # Fogo Cruzado (nomes sem prefixo, como o Luciano cadastrou no .env)
    fogo_cruzado_user: str = Field("", validation_alias="FOGO_CRUZADO_USER")
    fogo_cruzado_password: SecretStr = Field(
        SecretStr(""), validation_alias="FOGO_CRUZADO_PASSWORD"
    )

    # Chaves de fontes (fase 1+)
    openaq_api_key: SecretStr = SecretStr("")
    tomtom_api_key: SecretStr = SecretStr("")
    aisstream_api_key: SecretStr = SecretStr("")

    # LLM via OpenRouter. Sem chave, o enriquecimento por texto fica desligado e
    # o resto do produto segue igual — extração de texto é sempre acréscimo.
    openrouter_api_key: SecretStr = SecretStr("")
    # Escolhido por medição em 2026-08-07: oito modelos rodaram a mesma extração
    # real (comunicado do COR com cinco interdições). Todos acertaram os cinco
    # nomes; o que separou foi a vigência e o comedimento com coordenada.
    # O Sonnet acerta a janela de vigência, se RECUSA a chutar coordenada, e
    # gasta 625 tokens de saída contra os 2.009 do Gemini 3.6 Flash — que tem
    # raciocínio obrigatório e não dá pra desligar. Sai por metade do preço.
    # Descartados: deepseek-v4-flash (inventou data errada e cinco coordenadas),
    # deepseek-v4-pro (58 s por comunicado) e gemini-3.1-flash-lite (barato e
    # rápido, mas arrisca coordenadas que discordam entre modelos em até 12 km).
    llm_modelo: str = "anthropic/claude-sonnet-5"
    # Teto de segurança: acima disso o job para e loga, em vez de varrer a fila
    # inteira num dia ruim. O feed do COR publica ~10 posts/dia.
    llm_max_itens_por_rodada: int = 25

    # BigQuery do datalake `datario` (backfill histórico). A credencial em si é a
    # service account apontada por GOOGLE_APPLICATION_CREDENTIALS, que a
    # biblioteca do Google lê sozinha do ambiente.
    gcp_projeto: str = ""

    @property
    def llm_configurado(self) -> bool:
        return bool(self.openrouter_api_key.get_secret_value())

    @property
    def user_agent(self) -> str:
        return f"riolive/0.1 (coletor de dados abertos; contato: {self.contato})"


@lru_cache
def config() -> Config:
    return Config()
