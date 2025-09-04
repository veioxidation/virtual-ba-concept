#!/usr/bin/env python3
"""Database setup script to create all tables."""
import asyncio
from app.db.session import engine
from app.db.base import Base
from app.models import project, process, user, access, metrics


async def create_tables():
    """Create all database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_tables())
