from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "refurbops_dev"

    jwt_secret_key: str = "change-me"

    # Domain only. Endpoint paths belong in the integration layer.
    backmarket_base_url: str = "https://www.backmarket.co.uk"
    backmarket_timeout_seconds: float = 30.0

    file_storage_mode: str = "local"
    file_storage_path: str = "./storage"

    checkmend_base_url: str | None = None
    checkmend_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
