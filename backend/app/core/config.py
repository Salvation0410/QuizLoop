from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    database_url: str = "sqlite:///./quizeloop.db"
    closeai_base_url: str = "https://api.openai.com/v1"
    closeai_api_key: SecretStr = SecretStr("")
    llm_model: str = "gpt-5.4"
    llm_mode: str = "auto"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2
    cors_origins: str = "http://localhost:10086,http://127.0.0.1:10086"


@lru_cache
def get_settings() -> Settings:
    return Settings()
