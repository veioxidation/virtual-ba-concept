from __future__ import annotations

from app.schemas.common import ORMModel


class MetricValueOut(ORMModel):
    id: int
    metric_id: int
    process_id: int | None
    value_num: float | None
