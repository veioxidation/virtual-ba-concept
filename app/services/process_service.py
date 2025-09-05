from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.process import Process
from app.models.metrics import MetricValue
from app.repositories.process import ProcessRepository
from app.repositories.metrics import MetricValueRepository


class ProcessService:
    def __init__(self, session: AsyncSession):
        self.repo = ProcessRepository(session)
        self.metric_repo = MetricValueRepository(session)
        self.session = session

    async def list(self, *, offset: int = 0, limit: int = 50) -> list[Process]:
        return await self.repo.list(offset, limit)

    async def get(self, process_id: int) -> Process | None:
        return await self.repo.get(process_id)

    async def get_by_mod_guid(self, mod_guid: str) -> Process | None:
        return await self.repo.get_by_mod_guid(mod_guid)

    async def create(
        self,
        name: str,
        description: str | None,
        mod_guid: str | None = None,
        owner_id: int | None = None,
        is_public: bool = False,
    ) -> Process:
        obj = await self.repo.create(
            name=name,
            description=description,
            mod_guid=mod_guid,
            owner_id=owner_id,
            is_public=is_public,
        )
        await self.session.commit()
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
        obj = await self.repo.update(
            process_id,
            name=name,
            description=description,
            mod_guid=mod_guid,
            owner_id=owner_id,
            is_public=is_public,
        )
        await self.session.commit()
        return obj

    async def delete(self, process_id: int) -> None:
        await self.repo.delete(process_id)
        await self.session.commit()

    async def list_public(self, *, offset: int = 0, limit: int = 50) -> list[Process]:
        return await self.repo.list_public(offset, limit)

    async def list_by_owner(
        self, owner_id: int, *, offset: int = 0, limit: int = 50
    ) -> list[Process]:
        return await self.repo.list_by_owner(owner_id, offset, limit)

    async def make_public(self, process_id: int) -> Process | None:
        """Make a process public."""
        return await self.update(process_id, is_public=True)

    async def make_private(self, process_id: int) -> Process | None:
        """Make a process private."""
        return await self.update(process_id, is_public=False)

    async def transfer_ownership(
        self, process_id: int, new_owner_id: int
    ) -> Process | None:
        """Transfer ownership of a process to a new user."""
        return await self.update(process_id, owner_id=new_owner_id)

    async def list_metrics(
        self, process_id: int, *, offset: int = 0, limit: int = 50
    ) -> list[MetricValue]:
        """List metric values associated with a process."""
        return await self.metric_repo.list_by_process(process_id, offset, limit)
