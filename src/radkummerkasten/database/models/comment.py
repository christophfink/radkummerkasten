#!/usr/bin/env python3


"""The database model for comments on the radkummerkasten map."""

import datetime
import uuid
from typing import (
    List,
    Optional,
)

from sqlalchemy import (
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base

__all__ = ["Comment"]


class Comment(Base):
    """
    A comment attached to an issue reported to radkummerkasten map.

    Note that the first comment to an issue is shown as the issue text.
    """
    # pylint: disable=too-few-public-methods

    title: Mapped[Optional[str]]
    text: Mapped[str]

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), init=False)
    user: Mapped["User"] = relationship(  # noqa: F821
        default=None,
        # back_populates="comments"
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("issue.id"), init=False)

    media: Mapped[List["Media"]] = relationship(  # noqa: F821
        default_factory=list,
    )

    created: Mapped[datetime.datetime] = mapped_column(
        default_factory=datetime.datetime.now
    )
    updated: Mapped[datetime.datetime] = mapped_column(
        default_factory=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )
