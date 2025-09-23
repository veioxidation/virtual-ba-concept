from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
async def list_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    svc = UserService(session)
    return await svc.list(offset=offset, limit=limit)


@router.get("/active", response_model=list[UserOut])
async def list_active_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    svc = UserService(session)
    return await svc.list_active(offset=offset, limit=limit)


@router.post("/", response_model=UserOut, status_code=201)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    svc = UserService(session)
    return await svc.create(
        gpn=data.gpn,
        email=data.email,
        display_name=data.display_name,
        is_active=data.is_active,
        role=data.role,
        azure_oid=data.azure_oid,
    )


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
):
    svc = UserService(session)
    obj = await svc.get(user_id)
    if not obj:
        raise HTTPException(404, "User not found")
    if current_user.role != UserRole.ADMIN and current_user.id != obj.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enough permissions")
    return obj


@router.get("/by-gpn/{gpn}", response_model=UserOut)
async def get_user_by_gpn(
    gpn: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
):
    svc = UserService(session)
    obj = await svc.get_by_gpn(gpn)
    if not obj:
        raise HTTPException(404, "User not found")
    if current_user.role != UserRole.ADMIN and current_user.gpn != obj.gpn:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enough permissions")
    return obj


@router.get("/by-email/{email}", response_model=UserOut)
async def get_user_by_email(
    email: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
):
    svc = UserService(session)
    obj = await svc.get_by_email(email)
    if not obj:
        raise HTTPException(404, "User not found")
    if current_user.role != UserRole.ADMIN and current_user.email != obj.email:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enough permissions")
    return obj


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    data: UserUpdate,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    svc = UserService(session)
    obj = await svc.update(user_id, **data.model_dump(exclude_unset=True))
    if not obj:
        raise HTTPException(404, "User not found")
    return obj


@router.patch("/{user_id}/activate", response_model=UserOut)
async def activate_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    svc = UserService(session)
    obj = await svc.activate(user_id)
    if not obj:
        raise HTTPException(404, "User not found")
    return obj


@router.patch("/{user_id}/deactivate", response_model=UserOut)
async def deactivate_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    svc = UserService(session)
    obj = await svc.deactivate(user_id)
    if not obj:
        raise HTTPException(404, "User not found")
    return obj


@router.patch("/{user_id}/display-name", response_model=UserOut)
async def update_user_display_name(
    user_id: int,
    display_name: str,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    svc = UserService(session)
    obj = await svc.update_display_name(user_id, display_name)
    if not obj:
        raise HTTPException(404, "User not found")
    return obj


@router.patch("/{user_id}/email", response_model=UserOut)
async def update_user_email(
    user_id: int,
    email: str,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    svc = UserService(session)
    obj = await svc.update_email(user_id, email)
    if not obj:
        raise HTTPException(404, "User not found")
    return obj


@router.post("/get-or-create", response_model=UserOut)
async def get_or_create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    svc = UserService(session)
    return await svc.get_or_create_by_gpn(
        gpn=data.gpn,
        email=data.email,
        display_name=data.display_name,
        is_active=data.is_active,
        role=data.role,
        azure_oid=data.azure_oid,
    )


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    svc = UserService(session)
    await svc.delete(user_id)
