from __future__ import annotations
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager
from app.core.config import settings


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionMaker = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with AsyncSessionMaker() as session:
        yield session


@asynccontextmanager
async def lifespan_db():
    try:
        yield
    finally:
        await engine.dispose()