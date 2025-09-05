from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, func, DateTime, JSON, Boolean, UniqueConstraint
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.metrics import MetricValue


class Process(Base):
    id: Mapped[int] = mapped_column(primary_key=True)

    # Optional external join key from upstream (e.g., ARIS model GUID)
    mod_guid: Mapped[str | None] = mapped_column(String(64), index=True)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text())

    owner_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # One-to-many relationship with Project (one process can be used by many projects)
    projects: Mapped[list["Project"]] = relationship(back_populates="process")

    # Metrics associated with this process
    metrics: Mapped[list["MetricValue"]] = relationship(back_populates="process")

    __table_args__ = (
        UniqueConstraint("mod_guid", name="uq_process_mod_guid"),
    )
