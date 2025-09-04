from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class ProjectRole(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class ProjectAccess(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE")
    )
    role: Mapped[ProjectRole] = mapped_column(Enum(ProjectRole, native_enum=False))
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=no-member
    )

    user: Mapped["User"] = relationship(back_populates="project_accesses")
    project: Mapped["Project"] = relationship(back_populates="accesses")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "project_id", name="uq_project_access_user_project"
        ),
    )
