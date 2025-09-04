from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository


class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)
        self.session = session

    async def list(self, *, offset: int = 0, limit: int = 50) -> list[User]:
        return await self.repo.list(offset, limit)

    async def get(self, user_id: int) -> User | None:
        return await self.repo.get(user_id)

    async def get_by_gpn(self, gpn: str) -> User | None:
        return await self.repo.get_by_gpn(gpn)

    async def get_by_email(self, email: str) -> User | None:
        return await self.repo.get_by_email(email)

    async def create(
        self,
        gpn: str,
        email: str | None = None,
        display_name: str | None = None,
        is_active: bool = True,
    ) -> User:
        obj = await self.repo.create(
            gpn=gpn,
            email=email,
            display_name=display_name,
            is_active=is_active,
        )
        await self.session.commit()
        return obj

    async def update(
        self,
        user_id: int,
        *,
        gpn: str | None = None,
        email: str | None = None,
        display_name: str | None = None,
        is_active: bool | None = None,
    ) -> User | None:
        obj = await self.repo.update(
            user_id,
            gpn=gpn,
            email=email,
            display_name=display_name,
            is_active=is_active,
        )
        await self.session.commit()
        return obj

    async def delete(self, user_id: int) -> None:
        await self.repo.delete(user_id)
        await self.session.commit()

    async def list_active(self, *, offset: int = 0, limit: int = 50) -> list[User]:
        return await self.repo.list_active(offset, limit)

    async def deactivate(self, user_id: int) -> User | None:
        """Soft delete a user by setting is_active to False."""
        obj = await self.repo.deactivate(user_id)
        await self.session.commit()
        return obj

    async def activate(self, user_id: int) -> User | None:
        """Reactivate a user by setting is_active to True."""
        obj = await self.repo.activate(user_id)
        await self.session.commit()
        return obj

    async def update_display_name(self, user_id: int, display_name: str) -> User | None:
        """Update only the display name of a user."""
        return await self.update(user_id, display_name=display_name)

    async def update_email(self, user_id: int, email: str) -> User | None:
        """Update only the email of a user."""
        return await self.update(user_id, email=email)

    async def get_or_create_by_gpn(
        self,
        gpn: str,
        email: str | None = None,
        display_name: str | None = None,
    ) -> User:
        """Get existing user by GPN or create a new one."""
        user = await self.get_by_gpn(gpn)
        if user:
            return user

        return await self.create(
            gpn=gpn,
            email=email,
            display_name=display_name,
        )
