from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, offset: int = 0, limit: int = 50) -> list[User]:
        res = await self.session.execute(select(User).offset(offset).limit(limit))
        return list(res.scalars().all())

    async def get(self, user_id: int) -> User | None:
        res = await self.session.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()

    async def get_by_gpn(self, gpn: str) -> User | None:
        res = await self.session.execute(select(User).where(User.gpn == gpn))
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        res = await self.session.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return res.scalar_one_or_none()

    async def get_by_azure_oid(self, azure_oid: str) -> User | None:
        res = await self.session.execute(select(User).where(User.azure_oid == azure_oid))
        return res.scalar_one_or_none()

    async def create(
        self,
        gpn: str,
        *,
        email: str | None = None,
        display_name: str | None = None,
        is_active: bool = True,
        role: UserRole = UserRole.VIEWER,
        hashed_password: str | None = None,
        azure_oid: str | None = None,
    ) -> User:
        obj = User(
            gpn=gpn,
            email=email,
            display_name=display_name,
            is_active=is_active,
            hashed_password=hashed_password,
            role=role,
            azure_oid=azure_oid,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(
        self,
        user_id: int,
        *,
        gpn: str | None = None,
        email: str | None = None,
        display_name: str | None = None,
        is_active: bool | None = None,
        hashed_password: str | None = None,
        role: UserRole | None = None,
        azure_oid: str | None = None,
    ) -> User | None:
        update_data = {}
        if gpn is not None:
            update_data["gpn"] = gpn
        if email is not None:
            update_data["email"] = email
        if display_name is not None:
            update_data["display_name"] = display_name
        if is_active is not None:
            update_data["is_active"] = is_active
        if hashed_password is not None:
            update_data["hashed_password"] = hashed_password
        if role is not None:
            update_data["role"] = role
        if azure_oid is not None:
            update_data["azure_oid"] = azure_oid

        if not update_data:
            return await self.get(user_id)

        stmt = (
            update(User).where(User.id == user_id).values(**update_data).returning(User)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete(self, user_id: int) -> None:
        await self.session.execute(delete(User).where(User.id == user_id))

    async def list_active(self, offset: int = 0, limit: int = 50) -> list[User]:
        res = await self.session.execute(
            select(User).where(User.is_active == True).offset(offset).limit(limit)
        )
        return list(res.scalars().all())

    async def deactivate(self, user_id: int) -> User | None:
        """Soft delete by setting is_active to False."""
        return await self.update(user_id, is_active=False)

    async def activate(self, user_id: int) -> User | None:
        """Reactivate a user by setting is_active to True."""
        return await self.update(user_id, is_active=True)
