from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectWithReports


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectOut])
async def list_projects(offset: int = Query(0, ge=0),
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