from __future__ import annotations
from app.schemas.common import ORMModel
from app.schemas.report import ReportOut


class ProjectCreate(ORMModel):
    name: str
    description: str | None = None


class ProjectUpdate(ORMModel):
    name: str | None = None
    description: str | None = None


class ProjectOut(ORMModel):
    id: int
    name: str
    description: str | None
    process_id: int | None


class ProjectWithReports(ProjectOut):
    reports: list[ReportOut] = []