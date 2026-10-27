from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "FutureRoute AI"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    secret_key: str = Field(default="change-me-in-production")
    access_token_minutes: int = 60 * 8
    algorithm: str = "HS256"

    ors_api_key: str = ""
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    nominatim_base_url: str = "https://nominatim.openstreetmap.org/search"

    database_url: str = "postgresql+asyncpg://future:future@postgres:5432/futureroute"
    redis_url: str = "redis://redis:6379/0"

    rate_limit_per_minute: int = 90
    model_registry_dir: str = "ai_engine/artifacts"


@lru_cache
def get_settings() -> Settings:
    return Settings()

