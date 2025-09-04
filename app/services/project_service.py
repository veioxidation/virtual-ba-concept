from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.project import ProjectRepository
from app.repositories.report import ReportRepository
from app.models.project import Project, Report


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.repo = ProjectRepository(session)
        self.report_repo = ReportRepository(session)
        self.session = session


    async def list(
        self, process_id: int, *, offset: int = 0, limit: int = 50
    ) -> list[Project]:
        return await self.repo.list(process_id, offset, limit)


    async def get(self, project_id: int) -> Project | None:
        return await self.repo.get(project_id)


    async def create(
        self, process_id: int, name: str, description: str | None
    ) -> Project:
        obj = await self.repo.create(name, description, process_id)
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

    async def add_report(
        self,
        project_id: int,
        *,
        title: str,
        sections: dict,
        created_by_id: int | None = None,
        thread_id: str | None = None,
    ) -> Report:
        obj = await self.report_repo.create(
            project_id=project_id,
            title=title,
            sections=sections,
            created_by_id=created_by_id,
            thread_id=thread_id,
        )
        await self.session.commit()
        return obj