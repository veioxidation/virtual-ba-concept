from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, func, DateTime, Boolean, JSON, UniqueConstraint # type: ignore

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.access import ProjectAccess
    from app.models.process import Process
    from app.models.metrics import MetricValue

class Project(Base):
    """Project model representing a business process analysis project."""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text())
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="SET NULL"))
    process_id: Mapped[int | None] = mapped_column(ForeignKey("process.id", ondelete="SET NULL"), index=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=no-member
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) # pylint: disable=no-member


    owner: Mapped["User"] = relationship(back_populates="owned_projects")
    parent: Mapped["Project"] = relationship(remote_side=[id])
    accesses: Mapped[list["ProjectAccess"]] = relationship(back_populates="project", cascade="all, delete-orphan")


    reports: Mapped[list["Report"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    process: Mapped["Process"] = relationship(back_populates="projects")
    metrics: Mapped[list["MetricValue"]] = relationship(back_populates="project")


class Report(Base): 
    """Report model for storing analysis results from the Virtual BA."""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    # process_version_id: Mapped[int | None] = mapped_column(ForeignKey("processversion.id", ondelete="SET NULL"), index=True)

    title: Mapped[str] = mapped_column(String(200))
    
    # Free-form sections payload produced by the Virtual BA (e.g. overview, issues, questions, improvements)
    sections: Mapped[dict] = mapped_column(JSON, default=dict)

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=no-member
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) # pylint: disable=no-member

    # Optional linkage to a LangGraph run/thread for provenance
    thread_id: Mapped[str | None] = mapped_column(String(100))
    # run_id: Mapped[int | None] = mapped_column(ForeignKey("workflowrun.id", ondelete="SET NULL"))


    project: Mapped["Project"] = relationship(back_populates="reports")
    # process_version: Mapped["ProcessVersion" | None] = relationship(back_populates="reports")