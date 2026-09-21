"""Environment-backed application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Validated settings loaded from ``backend/.env`` and the environment."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "MindMate API"
    api_prefix: str = "/api"
    frontend_origin: str = "http://localhost:5173"
    max_request_body_bytes: int = Field(default=65_536, ge=1_024, le=10_485_760)

    firebase_project_id: str | None = None
    firebase_client_email: str | None = None
    firebase_private_key: SecretStr | None = None

    gemini_api_key: SecretStr | None = None
    gemini_text_model: str | None = None
    gemini_text_fallback_model: str | None = None
    gemini_live_model: str | None = None

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        """Keep route prefixes predictable and free of trailing slashes."""

        normalized = value.strip()
        if not normalized.startswith("/"):
            raise ValueError("API_PREFIX must start with '/'")
        if normalized != "/":
            normalized = normalized.rstrip("/")
        return normalized

    @field_validator("frontend_origin")
    @classmethod
    def validate_frontend_origin(cls, value: str) -> str:
        """Require a concrete HTTP origin because credentials are enabled."""

        normalized = value.strip().rstrip("/")
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("FRONTEND_ORIGIN must be an http:// or https:// origin")
        return normalized


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention settings instance per process."""

    return Settings()
