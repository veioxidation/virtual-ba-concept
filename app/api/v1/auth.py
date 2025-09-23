from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: CurrentUser) -> User:
    return current_user
