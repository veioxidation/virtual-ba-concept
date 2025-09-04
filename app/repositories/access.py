from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access import ProjectAccess, ProjectRole


class AccessRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, offset: int = 0, limit: int = 50) -> list[ProjectAccess]:
        res = await self.session.execute(
            select(ProjectAccess).offset(offset).limit(limit)
        )
        return list(res.scalars().all())

    async def get(self, access_id: int) -> ProjectAccess | None:
        res = await self.session.execute(
            select(ProjectAccess).where(ProjectAccess.id == access_id)
        )
        return res.scalar_one_or_none()

    async def get_by_user_and_project(
        self, user_id: int, project_id: int
    ) -> ProjectAccess | None:
        res = await self.session.execute(
            select(ProjectAccess).where(
                ProjectAccess.user_id == user_id, ProjectAccess.project_id == project_id
            )
        )
        return res.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        project_id: int,
        role: ProjectRole,
    ) -> ProjectAccess:
        obj = ProjectAccess(
            user_id=user_id,
            project_id=project_id,
            role=role,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(
        self,
        access_id: int,
        *,
        role: ProjectRole | None = None,
    ) -> ProjectAccess | None:
        update_data = {}
        if role is not None:
            update_data["role"] = role

        if not update_data:
            return await self.get(access_id)

        stmt = (
            update(ProjectAccess)
            .where(ProjectAccess.id == access_id)
            .values(**update_data)
            .returning(ProjectAccess)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete(self, access_id: int) -> None:
        await self.session.execute(
            delete(ProjectAccess).where(ProjectAccess.id == access_id)
        )

    async def delete_by_user_and_project(self, user_id: int, project_id: int) -> None:
        """Delete access by user and project combination."""
        await self.session.execute(
            delete(ProjectAccess).where(
                ProjectAccess.user_id == user_id, ProjectAccess.project_id == project_id
            )
        )

    async def list_by_project(
        self, project_id: int, offset: int = 0, limit: int = 50
    ) -> list[ProjectAccess]:
        """List all access entries for a specific project."""
        res = await self.session.execute(
            select(ProjectAccess)
            .where(ProjectAccess.project_id == project_id)
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())

    async def list_by_user(
        self, user_id: int, offset: int = 0, limit: int = 50
    ) -> list[ProjectAccess]:
        """List all access entries for a specific user."""
        res = await self.session.execute(
            select(ProjectAccess)
            .where(ProjectAccess.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())

    async def list_by_role(
        self, role: ProjectRole, offset: int = 0, limit: int = 50
    ) -> list[ProjectAccess]:
        """List all access entries with a specific role."""
        res = await self.session.execute(
            select(ProjectAccess)
            .where(ProjectAccess.role == role)
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())

    async def has_access(
        self, user_id: int, project_id: int, required_role: ProjectRole | None = None
    ) -> bool:
        """Check if a user has access to a project, optionally with a minimum role level."""
        access = await self.get_by_user_and_project(user_id, project_id)
        if not access:
            return False

        if required_role is None:
            return True

        # Role hierarchy: OWNER > EDITOR > VIEWER
        role_hierarchy = {
            ProjectRole.VIEWER: 1,
            ProjectRole.EDITOR: 2,
            ProjectRole.OWNER: 3,
        }

        user_role_level = role_hierarchy.get(access.role, 0)
        required_role_level = role_hierarchy.get(required_role, 0)

        return user_role_level >= required_role_level
