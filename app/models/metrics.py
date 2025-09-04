from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Float, DateTime, func, JSON, UniqueConstraint
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class MetricDef(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    unit: Mapped[str | None] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(String(500))


class MetricValue(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metricdef.id", ondelete="CASCADE"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    # process_version_id: Mapped[int | None] = mapped_column(ForeignKey("processversion.id", ondelete="CASCADE"), index=True)

    value_num: Mapped[float | None] = mapped_column(Float)
    # value_json: Mapped[dict | None] = mapped_column(JSON)

    # computed_by_run_id: Mapped[int | None] = mapped_column(ForeignKey("workflowrun.id", ondelete="SET NULL"))
    # computed_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    metric: Mapped["MetricDef"] = relationship()
    project: Mapped["Project"] = relationship(back_populates="metrics")
    # process_version: Mapped["ProcessVersion" | None] = relationship(back_populates="metrics")


    # __table_args__ = (
    #     UniqueConstraint("process_version_id", "metric_id", name="uq_metric_per_version"),
    # )