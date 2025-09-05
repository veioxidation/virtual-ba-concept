from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.project_service import ProjectService
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectOut,
    ProjectDetail,
)
from app.schemas.report import ReportCreate, ReportOut


router = APIRouter(prefix="/processes/{process_id}/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectDetail], response_model_exclude_unset=True)
async def list_projects(
    process_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    include_reports: bool = False,
    session: AsyncSession = Depends(get_db),
):
    svc = ProjectService(session)
    projects = await svc.list(
        process_id,
        offset=offset,
        limit=limit,
        include_reports=include_reports,
    )
    if include_reports:
        return [ProjectDetail.model_validate(p) for p in projects]
    return [ProjectOut.model_validate(p) for p in projects]


@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(
    process_id: int, data: ProjectCreate, session: AsyncSession = Depends(get_db)
):
    svc = ProjectService(session)
    return await svc.create(
        process_id=process_id, name=data.name, description=data.description
    )


@router.get(
    "/{project_id}",
    response_model=ProjectDetail,
    response_model_exclude_unset=True,
)
async def get_project(
    process_id: int,
    project_id: int,
    include_reports: bool = False,
    session: AsyncSession = Depends(get_db),
):
    svc = ProjectService(session)
    obj = await svc.get(project_id, include_reports=include_reports)
    if not obj or obj.process_id != process_id:
        raise HTTPException(404, "Project not found")
    if include_reports:
        return ProjectDetail.model_validate(obj)
    return ProjectOut.model_validate(obj)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    process_id: int,
    project_id: int,
    data: ProjectUpdate,
    session: AsyncSession = Depends(get_db),
):
    svc = ProjectService(session)
    existing = await svc.get(project_id)
    if not existing or existing.process_id != process_id:
        raise HTTPException(404, "Project not found")
    obj = await svc.update(project_id, **data.model_dump(exclude_unset=True))
    return obj


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    process_id: int, project_id: int, session: AsyncSession = Depends(get_db)
):
    svc = ProjectService(session)
    existing = await svc.get(project_id)
    if not existing or existing.process_id != process_id:
        raise HTTPException(404, "Project not found")
    await svc.delete(project_id)


@router.post(
    "/{project_id}/reports", response_model=ReportOut, status_code=201
)
async def add_report(
    process_id: int,
    project_id: int,
    data: ReportCreate,
    session: AsyncSession = Depends(get_db),
):
    svc = ProjectService(session)
    project = await svc.get(project_id)
    if not project or project.process_id != process_id:
        raise HTTPException(404, "Project not found")
    return await svc.add_report(
        project_id, title=data.title, sections=data.sections
    )


@router.get("/{project_id}/reports", response_model=list[ReportOut])
async def list_reports(
    process_id: int,
    project_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    svc = ProjectService(session)
    project = await svc.get(project_id)
    if not project or project.process_id != process_id:
        raise HTTPException(404, "Project not found")
    return await svc.list_reports(project_id, offset=offset, limit=limit)


