from __future__ import annotations
from typing import TYPE_CHECKING
from enum import StrEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint, Enum, DateTime, func
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project


class ProjectRole(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class ProjectAccess(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"))
    role: Mapped[ProjectRole] = mapped_column(Enum(ProjectRole, native_enum=False))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())


    user: Mapped["User"] = relationship(back_populates="project_accesses")
    project: Mapped["Project"] = relationship(back_populates="accesses")


    __table_args__ = (
    UniqueConstraint("user_id", "project_id", name="uq_project_access_user_project"),
    )

