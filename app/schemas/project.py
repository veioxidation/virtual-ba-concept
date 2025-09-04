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