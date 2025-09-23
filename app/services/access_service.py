from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access import ProjectAccess, ProjectRole
from app.repositories.access import AccessRepository
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository


class AccessNotFoundError(Exception):
    """Raised when a requested project access entry does not exist."""


class AccessService:
    """Service layer helpers for managing project-level access control."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.access_repo = AccessRepository(session)
        self.user_repo = UserRepository(session)
        self.project_repo = ProjectRepository(session)

    async def _ensure_project(self, project_id: int) -> None:
        project = await self.project_repo.get(project_id)
        if project is None:
            raise ValueError("Project not found")

    async def list_for_project(self, project_id: int) -> list[ProjectAccess]:
        await self._ensure_project(project_id)
        return await self.access_repo.list_by_project(project_id)

    async def grant_access(
        self,
        *,
        project_id: int,
        user_id: int,
        role: ProjectRole,
    ) -> ProjectAccess:
        await self._ensure_project(project_id)
        user = await self.user_repo.get(user_id)
        if user is None or not user.is_active:
            raise ValueError("Target user not found or inactive")
        if role == ProjectRole.OWNER:
            raise ValueError("Owner role cannot be granted via this endpoint")

        existing = await self.access_repo.get_by_user_and_project(user_id, project_id)
        if existing:
            access = await self.access_repo.update(existing.id, role=role)
        else:
            access = await self.access_repo.create(
                user_id=user_id,
                project_id=project_id,
                role=role,
            )
        await self.session.commit()
        if access is None:
            raise AccessNotFoundError("Unable to persist project access entry")
        return access

    async def revoke_access(self, *, project_id: int, user_id: int) -> None:
        await self._ensure_project(project_id)
        await self.access_repo.delete_by_user_and_project(user_id, project_id)
        await self.session.commit()

    async def get_access(
        self, *, project_id: int, user_id: int
    ) -> ProjectAccess | None:
        await self._ensure_project(project_id)
        return await self.access_repo.get_by_user_and_project(user_id, project_id)
