from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metrics import MetricDef, MetricValue


class MetricDefRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, offset: int = 0, limit: int = 50) -> list[MetricDef]:
        res = await self.session.execute(select(MetricDef).offset(offset).limit(limit))
        return list(res.scalars().all())

    async def get(self, metric_id: int) -> MetricDef | None:
        res = await self.session.execute(
            select(MetricDef).where(MetricDef.id == metric_id)
        )
        return res.scalar_one_or_none()

    async def get_by_name(self, name: str) -> MetricDef | None:
        res = await self.session.execute(
            select(MetricDef).where(MetricDef.name == name)
        )
        return res.scalar_one_or_none()

    async def create(
        self,
        name: str,
        unit: str | None = None,
        description: str | None = None,
    ) -> MetricDef:
        obj = MetricDef(
            name=name,
            unit=unit,
            description=description,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(
        self,
        metric_id: int,
        *,
        name: str | None = None,
        unit: str | None = None,
        description: str | None = None,
    ) -> MetricDef | None:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if unit is not None:
            update_data["unit"] = unit
        if description is not None:
            update_data["description"] = description

        if not update_data:
            return await self.get(metric_id)

        stmt = (
            update(MetricDef)
            .where(MetricDef.id == metric_id)
            .values(**update_data)
            .returning(MetricDef)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete(self, metric_id: int) -> None:
        await self.session.execute(delete(MetricDef).where(MetricDef.id == metric_id))


class MetricValueRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, offset: int = 0, limit: int = 50) -> list[MetricValue]:
        res = await self.session.execute(
            select(MetricValue).offset(offset).limit(limit)
        )
        return list(res.scalars().all())

    async def get(self, value_id: int) -> MetricValue | None:
        res = await self.session.execute(
            select(MetricValue).where(MetricValue.id == value_id)
        )
        return res.scalar_one_or_none()

    async def create(
        self,
        metric_id: int,
        process_id: int | None = None,
        value_num: float | None = None,
        value_json: dict | None = None,
    ) -> MetricValue:
        obj = MetricValue(
            metric_id=metric_id,
            process_id=process_id,
            value_num=value_num,
            value_json=value_json,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(
        self,
        value_id: int,
        *,
        value_num: float | None = None,
        value_json: dict | None = None,
    ) -> MetricValue | None:
        update_data = {}
        if value_num is not None:
            update_data["value_num"] = value_num
        if value_json is not None:
            update_data["value_json"] = value_json

        if not update_data:
            return await self.get(value_id)

        stmt = (
            update(MetricValue)
            .where(MetricValue.id == value_id)
            .values(**update_data)
            .returning(MetricValue)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete(self, value_id: int) -> None:
        await self.session.execute(
            delete(MetricValue).where(MetricValue.id == value_id)
        )

    async def list_by_process(
        self, process_id: int, offset: int = 0, limit: int = 50
    ) -> list[MetricValue]:
        """List all metric values for a specific process."""
        res = await self.session.execute(
            select(MetricValue)
            .where(MetricValue.process_id == process_id)
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())

    async def list_by_metric(
        self, metric_id: int, offset: int = 0, limit: int = 50
    ) -> list[MetricValue]:
        """List all values for a specific metric."""
        res = await self.session.execute(
            select(MetricValue)
            .where(MetricValue.metric_id == metric_id)
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())

    async def get_latest_by_process_and_metric(
        self, process_id: int, metric_id: int
    ) -> MetricValue | None:
        """Get the latest metric value for a specific process and metric."""
        res = await self.session.execute(
            select(MetricValue)
            .where(
                MetricValue.process_id == process_id, MetricValue.metric_id == metric_id
            )
            .order_by(MetricValue.computed_at.desc())
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def get_process_metrics_summary(self, process_id: int) -> list[MetricValue]:
        """Get the latest value for each metric in a process."""
        # This is a simplified version - in practice you might want to use a more complex query
        res = await self.session.execute(
            select(MetricValue)
            .where(MetricValue.process_id == process_id)
            .order_by(MetricValue.metric_id, MetricValue.computed_at.desc())
        )
        return list(res.scalars().all())
