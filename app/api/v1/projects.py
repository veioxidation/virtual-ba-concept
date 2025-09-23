from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.access import ProjectAccessOut, ProjectAccessUpdate
from app.schemas.project import (
    ProjectCreate,
    ProjectDetail,
    ProjectOut,
    ProjectUpdate,
)
from app.schemas.report import ReportCreate, ReportOut
from app.services.access_service import AccessService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/processes/{process_id}/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectDetail], response_model_exclude_unset=True)
async def list_projects(
    _: CurrentUser,
    process_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    include_reports: bool = False,
    include_metrics: bool = False,
    session: AsyncSession = Depends(get_db),
):
    svc = ProjectService(session)
    projects = await svc.list(
        process_id,
        offset=offset,
        limit=limit,
        include_reports=include_reports,
        include_metrics=include_metrics,
    )
    if include_reports or include_metrics:
        return [ProjectDetail.model_validate(p) for p in projects]
    return [ProjectOut.model_validate(p) for p in projects]


@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(
    process_id: int,
    data: ProjectCreate,
    _current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.PROJECT_MAINTAINER)
    ),
    session: AsyncSession = Depends(get_db),
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
    _: CurrentUser,
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
    _current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.PROJECT_MAINTAINER)
    ),
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
    process_id: int,
    project_id: int,
    _current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.PROJECT_MAINTAINER)
    ),
    session: AsyncSession = Depends(get_db),
):
    svc = ProjectService(session)
    existing = await svc.get(project_id)
    if not existing or existing.process_id != process_id:
        raise HTTPException(404, "Project not found")
    await svc.delete(project_id)


@router.get(
    "/{project_id}/access",
    response_model=list[ProjectAccessOut],
    response_model_exclude_unset=True,
)
async def list_project_access(
    process_id: int,
    project_id: int,
    _current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.PROJECT_MAINTAINER)
    ),
    session: AsyncSession = Depends(get_db),
):
    project_svc = ProjectService(session)
    project = await project_svc.get(project_id)
    if not project or project.process_id != process_id:
        raise HTTPException(404, "Project not found")

    access_svc = AccessService(session)
    try:
        return [
            ProjectAccessOut.model_validate(access)
            for access in await access_svc.list_for_project(project_id)
        ]
    except ValueError as exc:
        raise HTTPException(404, "Project not found") from exc


@router.put(
    "/{project_id}/access/{user_id}",
    response_model=ProjectAccessOut,
    status_code=200,
)
async def upsert_project_access(
    process_id: int,
    project_id: int,
    user_id: int,
    payload: ProjectAccessUpdate,
    _current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.PROJECT_MAINTAINER)
    ),
    session: AsyncSession = Depends(get_db),
):
    project_svc = ProjectService(session)
    project = await project_svc.get(project_id)
    if not project or project.process_id != process_id:
        raise HTTPException(404, "Project not found")

    access_svc = AccessService(session)
    try:
        access = await access_svc.grant_access(
            project_id=project_id,
            user_id=user_id,
            role=payload.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ProjectAccessOut.model_validate(access)


@router.delete(
    "/{project_id}/access/{user_id}",
    status_code=204,
)
async def revoke_project_access(
    process_id: int,
    project_id: int,
    user_id: int,
    _current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.PROJECT_MAINTAINER)
    ),
    session: AsyncSession = Depends(get_db),
):
    project_svc = ProjectService(session)
    project = await project_svc.get(project_id)
    if not project or project.process_id != process_id:
        raise HTTPException(404, "Project not found")

    access_svc = AccessService(session)
    try:
        await access_svc.revoke_access(project_id=project_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(404, "Project not found") from exc


@router.post("/{project_id}/reports", response_model=ReportOut, status_code=201)
async def add_report(
    process_id: int,
    project_id: int,
    data: ReportCreate,
    _current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.PROJECT_MAINTAINER)
    ),
    session: AsyncSession = Depends(get_db),
):
    svc = ProjectService(session)
    project = await svc.get(project_id)
    if not project or project.process_id != process_id:
        raise HTTPException(404, "Project not found")
    return await svc.add_report(project_id, title=data.title, sections=data.sections)


@router.get("/{project_id}/reports", response_model=list[ReportOut])
async def list_reports(
    _: CurrentUser,
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
