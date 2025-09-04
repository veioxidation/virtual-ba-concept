from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import MetaData

from app.core.config import settings

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata_obj = MetaData(naming_convention=convention,
                        schema=settings.schema)


class Base(DeclarativeBase):
    metadata = metadata_obj
    @declared_attr.directive
    def __tablename__(cls) -> str: # noqa
        return cls.__name__.lower()