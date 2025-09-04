# ─────────────────────────────────────────────────────────────────────────────
# Project layout (monorepo-friendly)
# ─────────────────────────────────────────────────────────────────────────────
# app/
#   __init__.py
#   main.py
#   core/
#       config.py
#       logging.py
#   db/
#       base.py
#       session.py
#   models/
#       project.py
#       report.py
#   schemas/
#       project.py
#       report.py
#       common.py
#   repositories/
#       project.py
#       report.py
#   services/
#       project_service.py
#       report_service.py
#   api/
#       deps.py
#       v1/
#           __init__.py
#           projects.py
#           reports.py
#           workflows.py
#   workflows/
#       __init__.py
#       state.py
#       graph.py
#       checkpointers.py
#       llm.py
#   instrumentation/
#       tracing.py
# pyproject.toml
# alembic.ini
# alembic/
#   env.py
#   versions/
# .env.example
# ─────────────────────────────────────────────────────────────────────────────

# ========================= pyproject.toml (minimal) ==========================
# [build-system]
# requires = ["setuptools", "wheel"]
# build-backend = "setuptools.build_meta"
#
# [project]
# name = "ai-workflows-api"
# version = "0.1.0"
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi>=0.115",
#   "uvicorn[standard]",
#   "pydantic>=2.7",
#   "pydantic-settings>=2",
#   "sqlalchemy[asyncio]>=2.0",
#   "asyncpg>=0.29",
#   "alembic>=1.13",
#   "structlog>=24",
#   "python-dotenv>=1",
#   "sse-starlette>=3.0.2",
#   "httpx>=0.27",
#   "orjson>=3",
#   "langgraph>=0.2",
#   "langchain>=0.2",
#   "langgraph-checkpoint-sqlite>=1.0",        # local/dev
#   "langgraph-checkpoint-postgres>=1.0",      # prod persistence
#   "psycopg[binary]>=3.2",                    # for Postgres checkpointer
# ]

# ============================= app/core/config.py ============================
from __future__ import annotations
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # FastAPI
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Database (application data)
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/appdb"

    # LangGraph checkpointer DB (can reuse application DB)
    langgraph_db_url: str | None = None  # e.g., "postgresql://user:pass@localhost:5432/appdb"
    use_sqlite_checkpointer: bool = True
    sqlite_checkpointer_path: str = "./.state.sqlite"

    # OpenAI or other model config (example)
    openai_api_key: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()

# ============================= app/core/logging.py ===========================
import logging, structlog

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    )

# ============================== app/db/base.py ===============================
from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import MetaData

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata_obj = MetaData(naming_convention=convention)

class Base(DeclarativeBase):
    metadata = metadata_obj
    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa
        return cls.__name__.lower()

# ============================= app/db/session.py =============================
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

# ============================= app/models/project.py =========================
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, func, DateTime, Boolean, JSON, UniqueConstraint
from app.db.base import Base

class Project(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text())
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="SET NULL"))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner: Mapped["User" | None] = relationship(back_populates="owned_projects")
    parent: Mapped["Project" | None] = relationship(remote_side=[id])
    accesses: Mapped[list["ProjectAccess"]] = relationship(back_populates="project", cascade="all, delete-orphan")

    reports: Mapped[list["Report"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    processes: Mapped[list["Process"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    metrics: Mapped[list["MetricValue"]] = relationship(back_populates="project")

class Report(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    # process_version_id: Mapped[int | None] = mapped_column(ForeignKey("processversion.id", ondelete="SET NULL"), index=True)

    title: Mapped[str] = mapped_column(String(200))
    # Free-form sections payload produced by the Virtual BA (e.g. overview, issues, questions, improvements)
    sections: Mapped[dict] = mapped_column(JSON, default=dict)

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Optional linkage to a LangGraph run/thread for provenance
    # thread_id: Mapped[str | None] = mapped_column(String(100))
    # run_id: Mapped[int | None] = mapped_column(ForeignKey("workflowrun.id", ondelete="SET NULL"))

    project: Mapped["Project"] = relationship(back_populates="reports")
    # process_version: Mapped["ProcessVersion" | None] = relationship(back_populates="reports")

# ============================= app/schemas/common.py =========================
from __future__ import annotations
from pydantic import BaseModel, ConfigDict

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# ============================ app/schemas/project.py =========================
from __future__ import annotations
from app.schemas.common import ORMModel

class ProjectCreate(ORMModel):
    name: str
    description: str | None = None

class ProjectUpdate(ORMModel):
    name: str | None = None
    description: str | None = None

class ReportOut(ORMModel):
    id: int
    title: str
    body: str

class ProjectOut(ORMModel):
    id: int
    name: str
    description: str | None

class ProjectWithReports(ProjectOut):
    reports: list[ReportOut] = []

# =========================== app/repositories/project.py =====================
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.project import Project, Report

class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, offset: int = 0, limit: int = 50) -> list[Project]:
        res = await self.session.execute(select(Project).offset(offset).limit(limit))
        return list(res.scalars().all())

    async def get(self, project_id: int) -> Project | None:
        res = await self.session.execute(select(Project).where(Project.id == project_id))
        return res.scalar_one_or_none()

    async def create(self, name: str, description: str | None) -> Project:
        obj = Project(name=name, description=description)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, project_id: int, *, name: str | None, description: str | None) -> Project | None:
        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(**{k: v for k, v in {"name": name, "description": description}.items() if v is not None})
            .returning(Project)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete(self, project_id: int) -> None:
        await self.session.execute(delete(Project).where(Project.id == project_id))

# ============================ app/services/project_service.py =================
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.project import ProjectRepository
from app.models.project import Project

class ProjectService:
    def __init__(self, session: AsyncSession):
        self.repo = ProjectRepository(session)
        self.session = session

    async def list(self, *, offset: int = 0, limit: int = 50) -> list[Project]:
        return await self.repo.list(offset, limit)

    async def get(self, project_id: int) -> Project | None:
        return await self.repo.get(project_id)

    async def create(self, name: str, description: str | None) -> Project:
        obj = await self.repo.create(name, description)
        await self.session.commit()
        return obj

    async def update(self, project_id: int, **kwargs) -> Project | None:
        obj = await self.repo.update(project_id, **kwargs)
        await self.session.commit()
        return obj

    async def delete(self, project_id: int) -> None:
        await self.repo.delete(project_id)
        await self.session.commit()

# ================================ app/api/deps.py ============================
from __future__ import annotations
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session

async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session

# ============================= app/api/v1/projects.py ========================
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectWithReports

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    svc = ProjectService(session)
    return await svc.list(offset=offset, limit=limit)

@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(data: ProjectCreate, session: AsyncSession = Depends(get_db)):
    svc = ProjectService(session)
    return await svc.create(name=data.name, description=data.description)

@router.get("/{project_id}", response_model=ProjectWithReports)
async def get_project(project_id: int, session: AsyncSession = Depends(get_db)):
    svc = ProjectService(session)
    obj = await svc.get(project_id)
    if not obj:
        raise HTTPException(404, "Project not found")
    return obj

@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: int, data: ProjectUpdate, session: AsyncSession = Depends(get_db)):
    svc = ProjectService(session)
    obj = await svc.update(project_id, **data.model_dump(exclude_unset=True))
    if not obj:
        raise HTTPException(404, "Project not found")
    return obj

@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, session: AsyncSession = Depends(get_db)):
    svc = ProjectService(session)
    await svc.delete(project_id)

# =============================== app/workflows/state.py ======================
from __future__ import annotations
from typing import TypedDict
from typing_extensions import Annotated
from operator import add

# Minimal shared state for a demo graph. Extend with your own channels.
class WorkflowState(TypedDict):
    messages: Annotated[list[dict], add]
    summary: str

# =============================== app/workflows/llm.py ========================
from __future__ import annotations
from langchain.chat_models import init_chat_model

# Using LangChain's new init_chat_model wrapper keeps vendor-agnostic imports
# while enabling token streaming with LangGraph.

def chat_model():
    # Configure via env vars, e.g. OPENAI_API_KEY; replace with azure, groq, etc.
    return init_chat_model(model="openai:gpt-4o-mini")

# ============================== app/workflows/checkpointers.py ===============
from __future__ import annotations
from app.core.config import settings

Checkpointer = object  # for type hints

async def build_checkpointer() -> Checkpointer:
    if settings.use_sqlite_checkpointer:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        return AsyncSqliteSaver(settings.sqlite_checkpointer_path)
    else:
        # Postgres production-grade checkpointer
        # Requires: pip install langgraph-checkpoint-postgres psycopg[binary]
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        return AsyncPostgresSaver(settings.langgraph_db_url or settings.database_url.replace("+asyncpg", ""))

# =============================== app/workflows/graph.py ======================
from __future__ import annotations
import operator
from typing import TypedDict
from typing_extensions import Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer
from app.workflows.state import WorkflowState
from app.workflows.llm import chat_model

# Define nodes

def summarize_node(state: WorkflowState):
    """Toy example: summarise accumulated messages.
    Demonstrates custom streaming inside a node (stream_mode="custom").
    """
    writer = get_stream_writer()
    writer({"progress": "summarizing"})
    text = "\n".join([m["content"] for m in state.get("messages", [])])
    llm = chat_model()
    resp = llm.invoke([{"role": "user", "content": f"Summarize: {text}"}])
    return {"summary": resp.content}

# Build & compile graph (no checkpointer here; injected in app.lifespan)

def build_graph():
    builder = StateGraph(WorkflowState)
    builder.add_node("summarize", summarize_node)
    builder.add_edge(START, "summarize")
    builder.add_edge("summarize", END)
    return builder

# =========================== app/api/v1/workflows.py =========================
from __future__ import annotations
import asyncio, json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sse_starlette import EventSourceResponse
from app.workflows.graph import build_graph
from app.workflows.checkpointers import build_checkpointer

router = APIRouter(prefix="/workflows", tags=["workflows"])

# Graph compiled at startup in lifespan and stored on app.state

def _graph(request: Request):
    g = request.app.state.graph
    if not g:
        raise HTTPException(500, "Graph not initialized")
    return g

@router.get("/{name}/state")
async def get_state(
    name: str,
    thread_id: str = Query(..., description="LangGraph thread id"),
    request: Request = None,
):
    graph = _graph(request)
    cfg = {"configurable": {"thread_id": thread_id}}
    snap = graph.get_state(cfg)
    return {"values": snap.values, "next": snap.next, "created_at": snap.created_at}

@router.post("/{name}/invoke")
async def invoke(
    name: str,
    payload: dict,
    thread_id: str = Query("default"),
    request: Request = None,
):
    graph = _graph(request)
    cfg = {"configurable": {"thread_id": thread_id}}
    out = graph.invoke(payload, cfg)
    return out

@router.post("/{name}/stream")
async def stream(
    name: str,
    payload: dict,
    thread_id: str = Query("default"),
    modes: list[str] = Query(["updates", "messages", "custom"]),
    request: Request | None = None,
):
    graph = _graph(request)
    cfg = {"configurable": {"thread_id": thread_id}}

    async def event_gen(req: Request):
        try:
            async for item in graph.astream(payload, cfg, stream_mode=modes):
                if await req.is_disconnected():
                    break
                # item may be a tuple (mode, chunk) or a single chunk depending on stream_mode
                if isinstance(item, tuple) and len(item) == 2:
                    mode, chunk = item
                    payload_obj = {"mode": mode, "data": _serialize(chunk)}
                else:
                    payload_obj = {"mode": modes[0], "data": _serialize(item)}
                yield {"event": "update", "data": json.dumps(payload_obj)}
        except asyncio.CancelledError:
            raise

    return EventSourceResponse(event_gen(request), headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# naive serializer for SSE JSON
def _serialize(x):
    try:
        if hasattr(x, "model_dump"):
            return x.model_dump()
        if isinstance(x, dict):
            return x
        return json.loads(json.dumps(x, default=str))
    except Exception:
        return str(x)

# ================================ app/main.py ================================
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.log import setup_logging
from app.db.session import lifespan_db
from app.api.v1 import projects as projects_router
from app.api.v1 import workflows as workflows_router
from app.workflows.graph import build_graph
from app.workflows.checkpointers import build_checkpointer

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # 1) initialize DB engine/session lifespan
    async with lifespan_db():
        # 2) compile graph with a real checkpointer
        builder = build_graph()
        checkpointer = await build_checkpointer()
        try:
            # For some checkpointers (e.g., Postgres) you may need a setup step
            if hasattr(checkpointer, "setup"):
                # sync saver has setup(); async saver has asetup()
                setup_coro = getattr(checkpointer, "asetup", None)
                if setup_coro:
                    await setup_coro()
                else:
                    checkpointer.setup()  # type: ignore
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

# =============================== .env.example ================================
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/appdb
# LANGGRAPH_DB_URL=postgresql://user:pass@localhost:5432/appdb
# USE_SQLITE_CHECKPOINTER=true
# SQLITE_CHECKPOINTER_PATH=.state.sqlite
# OPENAI_API_KEY=sk-...

# ============================== Alembic quickstart ===========================
# 1) alembic init alembic
# 2) configure alembic.ini sqlalchemy.url with DATABASE_URL (sync URL! e.g. postgresql+psycopg://...)
# 3) set target_metadata = Base.metadata in alembic/env.py
# 4) alembic revision --autogenerate -m "init"
# 5) alembic upgrade head

# ============================= React SSE consumer ============================
# Example hook for your Vite React app to consume streaming updates
# (put in: web/src/lib/useSSE.ts)
#
# export function useSSE(url: string, onMessage: (data: any) => void) {
#   useEffect(() => {
#     const es = new EventSource(url, { withCredentials: false });
#     es.onmessage = (ev) => {
#       try { onMessage(JSON.parse(ev.data)); } catch { /* no-op */ }
#     };
#     es.onerror = () => { es.close(); };
#     return () => es.close();
#   }, [url]);
# }

# ============================= cURL smoke tests ==============================
# Create a project
# curl -X POST http://localhost:8000/api/v1/projects/ \
#   -H 'content-type: application/json' \
#   -d '{"name":"demo","description":"first"}'
#
# Invoke a workflow
# curl -X POST 'http://localhost:8000/api/v1/workflows/summarizer/invoke?thread_id=t1' \
#   -H 'content-type: application/json' \
#   -d '{"messages":[{"role":"user","content":"Hello there"}]}'
#
# Stream a workflow (SSE)
# curl -N -X POST 'http://localhost:8000/api/v1/workflows/summarizer/stream?thread_id=t1' \
#   -H 'accept: text/event-stream' -H 'content-type: application/json' \
#   -d '{"messages":[{"role":"user","content":"Stream this please"}]}'
# =============================== app/models/user.py ==========================
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, func
from app.db.base import Base

class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    gpn: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # UBS Global Personnel Number
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    display_name: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owned_projects: Mapped[list["Project"]] = relationship(back_populates="owner")
    project_accesses: Mapped[list["ProjectAccess"]] = relationship(back_populates="user", cascade="all, delete-orphan")

# ============================== app/models/access.py =========================
from __future__ import annotations
from enum import StrEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint, Enum, DateTime, func
from app.db.base import Base

class ProjectRole(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

class ProjectAccess(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"))
    role: Mapped[ProjectRole] = mapped_column(Enum(ProjectRole, native_enum=False))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="project_accesses")
    project: Mapped["Project"] = relationship(back_populates="accesses")

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_project_access_user_project"),
    )

# ============================= app/models/process.py =========================
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, func, DateTime, JSON, Boolean, UniqueConstraint
from app.db.base import Base

class Process(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    mod_guid: Mapped[str] = mapped_column(String(64), index=True)  # ARIS model GUID
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text())

    external_source: Mapped[str] = mapped_column(String(50), default="ARIS")
    external_url: Mapped[str | None] = mapped_column(String(500))  # deep-link to ARIS

    owner_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="processes")
    versions: Mapped[list["ProcessVersion"]] = relationship(back_populates="process", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_id", "mod_guid", name="uq_process_project_mod"),
    )

class ProcessVersion(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    process_id: Mapped[int] = mapped_column(ForeignKey("process.id", ondelete="CASCADE"), index=True)

    # Optional upstream details
    aris_version: Mapped[str | None] = mapped_column(String(50))
    raw_aris_id: Mapped[int | None] = mapped_column(ForeignKey("arisraw.id", ondelete="SET NULL"))

    # Content hash to deduplicate identical versions
    content_hash: Mapped[str] = mapped_column(String(64), index=True)

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    process: Mapped["Process"] = relationship(back_populates="versions")
    steps: Mapped[list["ProcessStep"]] = relationship(back_populates="version", cascade="all, delete-orphan")
    edges: Mapped[list["ProcessEdge"]] = relationship(back_populates="version", cascade="all, delete-orphan")
    metrics: Mapped[list["MetricValue"]] = relationship(back_populates="process_version")
    reports: Mapped[list["Report"]] = relationship(back_populates="process_version")

class ProcessStep(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("processversion.id", ondelete="CASCADE"), index=True)
    step_guid: Mapped[str] = mapped_column(String(64), index=True)  # ARIS GUID for the node
    name: Mapped[str] = mapped_column(String(255))
    step_type: Mapped[str] = mapped_column(String(50))  # task / event / gateway / etc.
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)  # lane, role, system, coords, etc.
    order_index: Mapped[int | None]

    version: Mapped["ProcessVersion"] = relationship(back_populates="steps")

class ProcessEdge(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("processversion.id", ondelete="CASCADE"), index=True)
    source_step_id: Mapped[int] = mapped_column(ForeignKey("processstep.id", ondelete="CASCADE"))
    target_step_id: Mapped[int] = mapped_column(ForeignKey("processstep.id", ondelete="CASCADE"))
    edge_type: Mapped[str] = mapped_column(String(50))  # sequenceFlow / messageFlow / association
    label: Mapped[str | None] = mapped_column(String(255))
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)

    version: Mapped["ProcessVersion"] = relationship(back_populates="edges")

# =============================== app/models/aris_raw.py ======================
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, func, JSON
from app.db.base import Base

class ArisRaw(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    mod_guid: Mapped[str] = mapped_column(String(64), index=True)  # ARIS model GUID
    aris_version: Mapped[str | None] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON)  # full upstream JSON for reproducibility
    imported_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

# ============================== app/models/metrics.py ========================
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Float, DateTime, func, JSON, UniqueConstraint
from app.db.base import Base

class MetricDef(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    unit: Mapped[str | None] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(String(500))

class MetricValue(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metricdef.id", ondelete="CASCADE"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    process_version_id: Mapped[int | None] = mapped_column(ForeignKey("processversion.id", ondelete="CASCADE"), index=True)

    value_num: Mapped[float | None] = mapped_column(Float)
    value_json: Mapped[dict | None] = mapped_column(JSON)

    computed_by_run_id: Mapped[int | None] = mapped_column(ForeignKey("workflowrun.id", ondelete="SET NULL"))
    computed_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    metric: Mapped["MetricDef"] = relationship()
    project: Mapped["Project" | None] = relationship(back_populates="metrics")
    process_version: Mapped["ProcessVersion" | None] = relationship(back_populates="metrics")

    __table_args__ = (
        UniqueConstraint("process_version_id", "metric_id", name="uq_metric_per_version"),
    )

# ============================ app/models/workflow_run.py =====================
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, func, JSON
from app.db.base import Base

class WorkflowRun(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    graph_name: Mapped[str] = mapped_column(String(100))
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running/succeeded/failed

    input_: Mapped[dict] = mapped_column("input", JSON)
    output: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(String(500))

    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="SET NULL"), index=True)
    process_version_id: Mapped[int | None] = mapped_column(ForeignKey("processversion.id", ondelete="SET NULL"), index=True)

    started_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped["DateTime" | None] = mapped_column(DateTime(timezone=True))


