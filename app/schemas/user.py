from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.models.user import UserRole
from app.schemas.common import ORMModel


class UserCreate(ORMModel):
    gpn: str
    email: str | None = None
    display_name: str | None = None
    is_active: bool = True
    role: UserRole = UserRole.VIEWER
    azure_oid: str | None = Field(default=None, max_length=64)


class UserUpdate(ORMModel):
    gpn: str | None = None
    email: str | None = None
    display_name: str | None = None
    is_active: bool | None = None
    role: UserRole | None = None
    azure_oid: str | None = Field(default=None, max_length=64)


class UserOut(ORMModel):
    id: int
    gpn: str
    email: str | None
    display_name: str | None
    is_active: bool
    created_at: datetime
    role: UserRole
    azure_oid: str | None
