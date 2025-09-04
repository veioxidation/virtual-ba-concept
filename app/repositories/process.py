from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.process import Process


class ProcessRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, offset: int = 0, limit: int = 50) -> list[Process]:
        res = await self.session.execute(select(Process).offset(offset).limit(limit))
        return list(res.scalars().all())

    async def get(self, process_id: int) -> Process | None:
        res = await self.session.execute(
            select(Process).where(Process.id == process_id)
        )
        return res.scalar_one_or_none()

    async def get_by_mod_guid(self, mod_guid: str) -> Process | None:
        res = await self.session.execute(
            select(Process).where(Process.mod_guid == mod_guid)
        )
        return res.scalar_one_or_none()

    async def create(
        self,
        name: str,
        description: str | None,
        mod_guid: str | None = None,
        owner_id: int | None = None,
        is_public: bool = False,
    ) -> Process:
        obj = Process(
            name=name,
            description=description,
            mod_guid=mod_guid,
            owner_id=owner_id,
            is_public=is_public,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(
        self,
        process_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        mod_guid: str | None = None,
        owner_id: int | None = None,
        is_public: bool | None = None,
    ) -> Process | None:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if mod_guid is not None:
            update_data["mod_guid"] = mod_guid
        if owner_id is not None:
            update_data["owner_id"] = owner_id
        if is_public is not None:
            update_data["is_public"] = is_public

        if not update_data:
            return await self.get(process_id)

        stmt = (
            update(Process)
            .where(Process.id == process_id)
            .values(**update_data)
            .returning(Process)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete(self, process_id: int) -> None:
        await self.session.execute(delete(Process).where(Process.id == process_id))

    async def list_public(self, offset: int = 0, limit: int = 50) -> list[Process]:
        res = await self.session.execute(
            select(Process).where(Process.is_public == True).offset(offset).limit(limit)
        )
        return list(res.scalars().all())

    async def list_by_owner(
        self, owner_id: int, offset: int = 0, limit: int = 50
    ) -> list[Process]:
        res = await self.session.execute(
            select(Process)
            .where(Process.owner_id == owner_id)
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())
