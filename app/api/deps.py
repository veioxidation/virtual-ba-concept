from __future__ import annotations
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session