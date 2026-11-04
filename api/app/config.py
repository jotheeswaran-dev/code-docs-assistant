from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    answer_model: str = "claude-opus-5"
    bulk_model: str = "claude-haiku-4-5"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    store_path: str = "data/store.db"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
