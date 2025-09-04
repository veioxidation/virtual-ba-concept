from __future__ import annotations
from app.core.config import settings


Checkpointer = object # for type hints


async def build_checkpointer() -> Checkpointer:
    if settings.use_sqlite_checkpointer:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        return AsyncSqliteSaver(settings.sqlite_checkpointer_path)
    else:
        # Postgres production-grade checkpointer
        # Requires: pip install langgraph-checkpoint-postgres psycopg[binary]
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        return AsyncPostgresSaver(settings.langgraph_db_url or settings.database_url.replace("+asyncpg", ""))