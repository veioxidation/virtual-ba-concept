from __future__ import annotations

from app.schemas.common import ORMModel


class ReportCreate(ORMModel):
    title: str
    sections: dict


class ReportOut(ORMModel):
    id: int
    title: str
    sections: dict
