"""Application configuration via pydantic-settings.

Reads from environment variables. See .env.example for the full list.
"""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the mini-bank backend."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="sqlite:///./minibank.db",
        description="SQLAlchemy DSN. sqlite:///./minibank.db for dev, postgresql+psycopg://... for prod.",
    )
    jwt_secret: str = Field(
        default="dev-only-jwt-secret-change-me",
        description="HMAC secret for JWT signing. MUST be overridden in prod.",
    )
    jwt_algorithm: str = "HS256"
    jwt_ttl_minutes: int = 60
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    environment: str = "dev"
    pln_per_eur: Decimal = Decimal("4.30")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
