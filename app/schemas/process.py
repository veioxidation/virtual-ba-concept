from __future__ import annotations

from datetime import datetime

from app.schemas.common import ORMModel


class ProcessCreate(ORMModel):
    name: str
    description: str | None = None
    mod_guid: str | None = None
    owner_id: int | None = None
    is_public: bool = False


class ProcessUpdate(ORMModel):
    name: str | None = None
    description: str | None = None
    mod_guid: str | None = None
    owner_id: int | None = None
    is_public: bool | None = None


class ProcessOut(ORMModel):
    id: int
    name: str
    description: str | None
    mod_guid: str | None
    owner_id: int | None
    is_public: bool
    created_at: datetime
    updated_at: datetime
