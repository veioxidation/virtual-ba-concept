from __future__ import annotations

from typing import Annotated, Any, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    InvalidTokenError,
    bearer_scheme,
    decode_access_token,
)
from app.db.session import get_session
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import TokenPayload


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


def _highest_role_from_claims(claims: list[str] | str | None) -> UserRole | None:
    if not claims:
        return None
    if isinstance(claims, str):
        normalized = {claims.lower()}
    else:
        normalized = {claim.lower() for claim in claims}
    priority = (
        UserRole.ADMIN,
        UserRole.PROJECT_MAINTAINER,
        UserRole.PROCESS_CREATOR,
        UserRole.VIEWER,
    )
    for candidate in priority:
        if candidate.value in normalized:
            return candidate
    return None


def _emails_from_token(token: TokenPayload) -> list[str]:
    emails: list[str] = []
    for value in (
        token.email,
        token.preferred_username,
        token.upn,
    ):
        if value:
            emails.append(value.lower())
    if token.emails:
        emails.extend(email.lower() for email in token.emails if email)
    # Preserve order but drop duplicates
    return list(dict.fromkeys(emails))


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    session: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_exception

    try:
        payload = await decode_access_token(credentials.credentials)
        token_data = TokenPayload.model_validate(payload)
    except InvalidTokenError as exc:
        raise credentials_exception from exc

    repo = UserRepository(session)
    user: User | None = None

    lookups: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def enqueue(kind: str, value: str | None) -> None:
        if value:
            key = (kind, value)
            if key not in seen:
                seen.add(key)
                lookups.append(key)

    enqueue("azure_oid", token_data.oid)
    enqueue("azure_oid", token_data.sub)
    enqueue("gpn", token_data.sub)
    for email in _emails_from_token(token_data):
        enqueue("email", email)

    for kind, value in lookups:
        if kind == "azure_oid":
            user = await repo.get_by_azure_oid(value)
        elif kind == "gpn":
            user = await repo.get_by_gpn(value)
        else:
            user = await repo.get_by_email(value)
        if user:
            break

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is not registered",
        )

    updates: dict[str, Any] = {}
    if token_data.oid and user.azure_oid != token_data.oid:
        updates["azure_oid"] = token_data.oid
    emails = _emails_from_token(token_data)
    if emails and not user.email:
        updates["email"] = emails[0]
    if token_data.name and not user.display_name:
        updates["display_name"] = token_data.name

    claimed_role = _highest_role_from_claims(token_data.roles)
    if claimed_role and user.role != claimed_role:
        updates["role"] = claimed_role

    if updates:
        updated = await repo.update(user.id, **updates)
        await session.commit()
        if updated is not None:
            user = updated

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    async def dependency(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if not roles:
            return current_user
        if current_user.role == UserRole.ADMIN or current_user.role in roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return dependency


CurrentUser = Annotated[User, Depends(get_current_active_user)]
