#!/usr/bin/env python3


"""The database model for issues on the radkummerkasten map."""

import datetime
import uuid
from typing import List

from sqlalchemy import (
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base
from .issue_type import IssueType

__all__ = ["Issue"]


class Issue(Base):
    """
    An issue reported to radkummerkasten map.

    Note that the first comment to this issue is shown as the issue text.
    """
    # pylint: disable=too-few-public-methods

    issue_type: Mapped[IssueType]

    lon: Mapped[float]
    lat: Mapped[float]

    created: Mapped[datetime.datetime] = mapped_column(
        default_factory=datetime.datetime.now
    )
    updated: Mapped[datetime.datetime] = mapped_column(
        default_factory=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )

    comments: Mapped[List["Comment"]] = relationship(  # noqa: F821
        # back_populates="issue",
        default_factory=list,
    )

    likes: Mapped[int] = mapped_column(default=0)

    address_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("address.id"),
        init=False,
    )
    address: Mapped["Address"] = relationship(  # noqa: F821
        # back_populates="issues",
        default=None,
    )
