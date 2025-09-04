from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.log import setup_logging
from app.db.session import lifespan_db, engine
from app.db.base import Base
from app.api.v1 import projects as projects_router
from app.api.v1 import workflows as workflows_router
from app.workflows.graph import build_graph
from app.workflows.checkpointer import build_checkpointer

# Import all models to ensure they're registered with Base.metadata
from app.models import project, process, user, access, metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # 1) initialize DB engine/session lifespan
    async with lifespan_db():
        # 2) create database tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 3) compile graph with a real checkpointer
        builder = build_graph()
        checkpointer = await build_checkpointer()
        try:
            # For some checkpointers (e.g., Postgres) you may need a setup step
            setup_coro = None
            if hasattr(checkpointer, "setup"):
                # sync saver has setup(); async saver has asetup()
                setup_coro = getattr(checkpointer, "asetup", None)
            if setup_coro:
                await setup_coro()
            else:
                checkpointer.setup() # type: ignore
        except Exception:
            # Often safe to ignore if tables already exist
            pass
        app.state.graph = builder.compile(checkpointer=checkpointer)
        yield
        # teardown handled by lifespan_db


app = FastAPI(title="AI Workflows API", version="0.1.0", lifespan=lifespan)


# CORS for your Vite React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(projects_router.router, prefix=settings.api_v1_prefix)
app.include_router(workflows_router.router, prefix=settings.api_v1_prefix)