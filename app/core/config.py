from __future__ import annotations

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

import secrets


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    # FastAPI
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    azure_frontend_app_url: str | None = None

    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    # Azure Active Directory (JWT validation)
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_audience: str | None = None
    azure_authority_host: str = "https://login.microsoftonline.com"
    azure_openid_cache_seconds: int = 3600

    # Database (application data)
    database_driver: str = "postgresql+asyncpg"
    database_user: str = "automation"
    database_password: str = "automation123"
    database_host: str = "localhost"
    database_port: int = 5434
    database_name: str = "postgres"
    db_schema: str = "goptic"

    # LangGraph checkpointer DB (can reuse application DB)
    langgraph_db_url: str | None = None  # e.g., "postgresql://user:pass@localhost:5432/appdb"
    use_sqlite_checkpointer: bool = True
    sqlite_checkpointer_path: str = "./.state.sqlite"

    # OpenAI or other model config (example)
    openai_api_key: str | None = None

    # Allow overriding settings via a local .env file or environment variables
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Allow providing CORS origins as a comma separated string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        return []

    @property
    def database_url(self) -> str:
        """Assemble the database connection URL from individual components."""
        return (
            f"{self.database_driver}://"
            f"{self.database_user}:{self.database_password}@"
            f"{self.database_host}:{self.database_port}/"
            f"{self.database_name}"
        )

    @property
    def allowed_cors_origins(self) -> list[str]:
        """Return the list of CORS origins including optional Azure front-end."""
        origins: list[str] = list(dict.fromkeys(self.cors_origins))
        if self.azure_frontend_app_url:
            origin = self.azure_frontend_app_url.rstrip("/")
            if origin not in origins:
                origins.append(origin)
        return origins

    @property
    def azure_expected_audience(self) -> str | None:
        """Return the expected audience for Azure-issued tokens."""
        if self.azure_audience:
            return self.azure_audience
        return self.azure_client_id


settings = Settings()

