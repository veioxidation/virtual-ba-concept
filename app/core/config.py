from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    # FastAPI
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

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

    @property
    def database_url(self) -> str:
        """Assemble the database connection URL from individual components."""
        return (
            f"{self.database_driver}://"
            f"{self.database_user}:{self.database_password}@"
            f"{self.database_host}:{self.database_port}/"
            f"{self.database_name}"
        )


settings = Settings()

