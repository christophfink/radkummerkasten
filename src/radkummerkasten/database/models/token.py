#!/usr/bin/env python3


"""The database model for auth tokens on the radkummerkasten map."""

import datetime
import secrets
import uuid

from sqlalchemy import (
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base

__all__ = ["Token"]

DEFAULT_EXPIRATION_DURATION = datetime.timedelta(minutes=15)


class Token(Base):
    """An auth token."""
    # pylint: disable=too-few-public-methods

    token: Mapped[str] = mapped_column(
        default_factory=lambda: secrets.token_urlsafe(32)
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), init=False)
    user: Mapped["User"] = relationship(default=None)  # noqa: F821

    next_url: Mapped[str] = mapped_column(default=None)

    created: Mapped[datetime.datetime] = mapped_column(
        default_factory=datetime.datetime.now
    )
    expires: Mapped[datetime.datetime] = mapped_column(
        default_factory=lambda: (datetime.datetime.now() + DEFAULT_EXPIRATION_DURATION)
    )
    used: Mapped[datetime.datetime] = mapped_column(default=None, nullable=True)
