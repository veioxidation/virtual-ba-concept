from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.project import Project, Report

class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def list(self, process_id: int, offset: int = 0, limit: int = 50) -> list[Project]:
        res = await self.session.execute(
            select(Project)
            .where(Project.process_id == process_id)
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())


    async def get(self, project_id: int) -> Project | None:
        res = await self.session.execute(select(Project).where(Project.id == project_id))
        return res.scalar_one_or_none()


    async def create(
        self, name: str, description: str | None, process_id: int
    ) -> Project:
        obj = Project(name=name, description=description, process_id=process_id)
        self.session.add(obj)
        await self.session.flush()
        return obj


    async def update(
        self, project_id: int, *, name: str | None, description: str | None
    ) -> Project | None:
        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(
                **{
                    k: v
                    for k, v in {"name": name, "description": description}.items()
                    if v is not None
                }
            )
            .returning(Project)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()


    async def delete(self, project_id: int) -> None:
        await self.session.execute(delete(Project).where(Project.id == project_id))
