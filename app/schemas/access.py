from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.models.access import ProjectRole
from app.schemas.common import ORMModel


class ProjectAccessBase(ORMModel):
    role: ProjectRole

    @field_validator("role")
    @classmethod
    def reject_owner_role(cls, value: ProjectRole) -> ProjectRole:
        """Only editor/viewer roles can be assigned via the API."""
        if value == ProjectRole.OWNER:
            raise ValueError("Owner role cannot be assigned via project access API")
        return value


class ProjectAccessCreate(ProjectAccessBase):
    user_id: int


class ProjectAccessUpdate(ProjectAccessBase):
    pass


class ProjectAccessOut(ProjectAccessBase):
    id: int
    project_id: int
    user_id: int
    created_at: datetime | None = Field(default=None)
