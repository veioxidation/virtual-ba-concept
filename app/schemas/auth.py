from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict

from app.schemas.common import ORMModel


class TokenPayload(ORMModel):
    aud: str | list[str] | None = None
    tid: str | None = None
    sub: str | None = None
    oid: str | None = None
    preferred_username: str | None = None
    upn: str | None = None
    email: str | None = None
    emails: list[str] | None = None
    name: str | None = None
    roles: list[str] | None = None
    exp: datetime | None = None

    model_config = ConfigDict(extra="allow")
