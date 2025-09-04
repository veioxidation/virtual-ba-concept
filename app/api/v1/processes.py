from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.process import ProcessCreate, ProcessOut, ProcessUpdate
from app.services.process_service import ProcessService

router = APIRouter(prefix="/processes", tags=["processes"])


@router.get("/", response_model=list[ProcessOut])
async def list_processes(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    svc = ProcessService(session)
    return await svc.list(offset=offset, limit=limit)


@router.get("/public", response_model=list[ProcessOut])
async def list_public_processes(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    svc = ProcessService(session)
    return await svc.list_public(offset=offset, limit=limit)


@router.get("/by-owner/{owner_id}", response_model=list[ProcessOut])
async def list_processes_by_owner(
    owner_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    svc = ProcessService(session)
    return await svc.list_by_owner(owner_id, offset=offset, limit=limit)


@router.post("/", response_model=ProcessOut, status_code=201)
async def create_process(data: ProcessCreate, session: AsyncSession = Depends(get_db)):
    svc = ProcessService(session)
    return await svc.create(
        name=data.name,
        description=data.description,
        mod_guid=data.mod_guid,
        owner_id=data.owner_id,
        is_public=data.is_public,
    )


@router.get("/{process_id}", response_model=ProcessOut)
async def get_process(process_id: int, session: AsyncSession = Depends(get_db)):
    svc = ProcessService(session)
    obj = await svc.get(process_id)
    if not obj:
        raise HTTPException(404, "Process not found")
    return obj


@router.get("/by-guid/{mod_guid}", response_model=ProcessOut)
async def get_process_by_guid(mod_guid: str, session: AsyncSession = Depends(get_db)):
    svc = ProcessService(session)
    obj = await svc.get_by_mod_guid(mod_guid)
    if not obj:
        raise HTTPException(404, "Process not found")
    return obj


@router.patch("/{process_id}", response_model=ProcessOut)
async def update_process(
    process_id: int, data: ProcessUpdate, session: AsyncSession = Depends(get_db)
):
    svc = ProcessService(session)
    obj = await svc.update(process_id, **data.model_dump(exclude_unset=True))
    if not obj:
        raise HTTPException(404, "Process not found")
    return obj


@router.patch("/{process_id}/make-public", response_model=ProcessOut)
async def make_process_public(process_id: int, session: AsyncSession = Depends(get_db)):
    svc = ProcessService(session)
    obj = await svc.make_public(process_id)
    if not obj:
        raise HTTPException(404, "Process not found")
    return obj


@router.patch("/{process_id}/make-private", response_model=ProcessOut)
async def make_process_private(
    process_id: int, session: AsyncSession = Depends(get_db)
):
    svc = ProcessService(session)
    obj = await svc.make_private(process_id)
    if not obj:
        raise HTTPException(404, "Process not found")
    return obj


@router.patch("/{process_id}/transfer-ownership", response_model=ProcessOut)
async def transfer_process_ownership(
    process_id: int, new_owner_id: int, session: AsyncSession = Depends(get_db)
):
    svc = ProcessService(session)
    obj = await svc.transfer_ownership(process_id, new_owner_id)
    if not obj:
        raise HTTPException(404, "Process not found")
    return obj


@router.delete("/{process_id}", status_code=204)
async def delete_process(process_id: int, session: AsyncSession = Depends(get_db)):
    svc = ProcessService(session)
    await svc.delete(process_id)
