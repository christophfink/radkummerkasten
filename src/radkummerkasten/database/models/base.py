#!/usr/bin/env python3


"""A common sqlalchemy DeclarativeBase to share between models."""

__all__ = ["Base"]


import re
import uuid

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    declared_attr,
    mapped_column,
)

CAMEL_CASE_TO_SNAKE_CASE_RE = re.compile(
    "((?<=[a-z0-9])[A-Z]|(?!^)(?<!_)[A-Z](?=[a-z]))"
)


def snake_case(camel_case):
    """Convert a `CamelCase` string to `snake_case`."""
    return CAMEL_CASE_TO_SNAKE_CASE_RE.sub(r"_\1", camel_case).lower()


class Base(DeclarativeBase, MappedAsDataclass):
    """Template for sqlalchemy declarative_base() to add shared functionality."""
    # pylint: disable=too-few-public-methods

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        init=False,
        default_factory=uuid.uuid4,
    )

    @declared_attr.directive
    def __tablename__(cls):  # pylint: disable=no-self-argument
        """Return a table name derived from the class name."""
        return f"{snake_case(cls.__name__)}"
