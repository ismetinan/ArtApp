from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ai_provider: str = "mock"  # mock | gemini (ileride: claude, openai)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    database_url: str = "postgresql+psycopg://artapp:artapp@localhost:5433/artapp"
    redis_url: str = "redis://localhost:6379/0"
    storage_dir: str = "./storage"

    mentor_market_enabled: bool = False  # Faz 2'de açılacak


@lru_cache
def get_settings() -> Settings:
    return Settings()
