from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Report


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, offset: int = 0, limit: int = 50) -> list[Report]:
        res = await self.session.execute(select(Report).offset(offset).limit(limit))
        return list(res.scalars().all())

    async def get(self, report_id: int) -> Report | None:
        res = await self.session.execute(select(Report).where(Report.id == report_id))
        return res.scalar_one_or_none()

    async def get_latest_by_project(self, project_id: int) -> Report | None:
        """Get the latest report for a specific project."""
        res = await self.session.execute(
            select(Report)
            .where(Report.project_id == project_id)
            .order_by(Report.created_at.desc())
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def create(
        self,
        project_id: int,
        title: str,
        sections: dict,
        created_by_id: int | None = None,
        thread_id: str | None = None,
    ) -> Report:
        obj = Report(
            project_id=project_id,
            title=title,
            sections=sections,
            created_by_id=created_by_id,
            thread_id=thread_id,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(
        self,
        report_id: int,
        *,
        title: str | None = None,
        sections: dict | None = None,
        thread_id: str | None = None,
    ) -> Report | None:
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if sections is not None:
            update_data["sections"] = sections
        if thread_id is not None:
            update_data["thread_id"] = thread_id

        if not update_data:
            return await self.get(report_id)

        stmt = (
            update(Report)
            .where(Report.id == report_id)
            .values(**update_data)
            .returning(Report)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete(self, report_id: int) -> None:
        await self.session.execute(delete(Report).where(Report.id == report_id))

    async def list_by_project(
        self, project_id: int, offset: int = 0, limit: int = 50
    ) -> list[Report]:
        """List all reports for a specific project."""
        res = await self.session.execute(
            select(Report)
            .where(Report.project_id == project_id)
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())

    async def list_by_creator(
        self, created_by_id: int, offset: int = 0, limit: int = 50
    ) -> list[Report]:
        """List all reports created by a specific user."""
        res = await self.session.execute(
            select(Report)
            .where(Report.created_by_id == created_by_id)
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())

    async def get_by_thread_id(self, thread_id: str) -> Report | None:
        """Get report by LangGraph thread ID."""
        res = await self.session.execute(
            select(Report).where(Report.thread_id == thread_id)
        )
        return res.scalar_one_or_none()

    async def update_sections(self, report_id: int, sections: dict) -> Report | None:
        """Update only the sections of a report."""
        return await self.update(report_id, sections=sections)

    async def add_section(
        self, report_id: int, section_name: str, section_content: dict
    ) -> Report | None:
        """Add a new section to an existing report."""
        report = await self.get(report_id)
        if not report:
            return None

        # Create a copy of existing sections and add the new one
        updated_sections = report.sections.copy()
        updated_sections[section_name] = section_content

        return await self.update(report_id, sections=updated_sections)
