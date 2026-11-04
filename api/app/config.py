from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    answer_model: str = "claude-opus-5"
    bulk_model: str = "claude-haiku-4-5"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_cache: str = ".models"
    store_path: str = "data/store.db"
    context_budget_chars: int = 60_000
    max_answer_tokens: int = 8192

    # The published rates for the answer model, in dollars for each million tokens.
    price_input_per_mtok: float = 5.0
    price_output_per_mtok: float = 25.0
    price_cache_read_per_mtok: float = 0.50
    price_cache_write_per_mtok: float = 6.25
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
