from __future__ import annotations

from datetime import datetime

from app.schemas.common import ORMModel


class UserCreate(ORMModel):
    gpn: str
    email: str | None = None
    display_name: str | None = None
    is_active: bool = True


class UserUpdate(ORMModel):
    gpn: str | None = None
    email: str | None = None
    display_name: str | None = None
    is_active: bool | None = None


class UserOut(ORMModel):
    id: int
    gpn: str
    email: str | None
    display_name: str | None
    is_active: bool
    created_at: datetime
