from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.project import ProjectRepository
from app.models.project import Project


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.repo = ProjectRepository(session)
        self.session = session


    async def list(self, *, offset: int = 0, limit: int = 50) -> list[Project]:
        return await self.repo.list(offset, limit)


    async def get(self, project_id: int) -> Project | None:
        return await self.repo.get(project_id)


    async def create(self, name: str, description: str | None) -> Project:
        obj = await self.repo.create(name, description)
        await self.session.commit()
        return obj


    async def update(self, project_id: int, **kwargs) -> Project | None:
        obj = await self.repo.update(
            project_id, 
            name=kwargs.get('name'), 
            description=kwargs.get('description')
        )
        await self.session.commit()
        return obj


    async def delete(self, project_id: int) -> None:
        await self.repo.delete(project_id)
        await self.session.commit()