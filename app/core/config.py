from __future__ import annotations
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # FastAPI
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


    # Database (application data)
    database_url: str = "postgresql+asyncpg://automation:automation123@localhost:5434/postgres"
    schema: str = "goptic"

    # LangGraph checkpointer DB (can reuse application DB)
    langgraph_db_url: str | None = None # e.g., "postgresql://user:pass@localhost:5432/appdb"
    use_sqlite_checkpointer: bool = True
    sqlite_checkpointer_path: str = "./.state.sqlite"


    # OpenAI or other model config (example)
    openai_api_key: str | None = None


    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields instead of raising an error   


settings = Settings()