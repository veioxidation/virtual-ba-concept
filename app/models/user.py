from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.access import ProjectAccess
    from app.models.project import Project


class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    gpn: Mapped[str] = mapped_column(
        String(64), unique=True, index=True
    )  # UBS Global Personnel Number
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    display_name: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # pylint: disable=no-member

    owned_projects: Mapped[list["Project"]] = relationship(back_populates="owner")
    project_accesses: Mapped[list["ProjectAccess"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
