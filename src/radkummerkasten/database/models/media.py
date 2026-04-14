#!/usr/bin/env python3


"""The database model for media attached to comments on the radkummerkasten map."""

import pathlib
import uuid

import flask
from PIL import (
    Image,
)
from sqlalchemy import (
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from .base import Base

__all__ = ["Media"]


MEDIA_SIZE = (1280, 1280)


class Media(Base):
    """
    Some media attached to a comment on the radkummerkasten map.

    Currently restricted to photos/images.
    """
    # pylint: disable=too-few-public-methods

    comment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("comment.id"),
        init=False,
    )

    @classmethod
    def from_image_file(cls, image_file, instance_path=None):
        """
        Create a new instance from a file or file handle.

        Arguments
        ---------
        image_file: os.PathLike | typing.BinaryIO
            The image file to load this media item from
        instance_path: os.PathLike
            The application’s instance path (used to determine where
            to save the image file)
        """
        if instance_path is None:
            try:
                instance_path = pathlib.Path(flask.current_app.instance_path)
            except RuntimeError as exception:
                # RuntimeError: Working outside of application context.
                raise RuntimeError(
                    "When using Media.from_image_file() outside of "
                    "an application context, pass an instance_path."
                ) from exception
        image = Image.open(image_file)
        image.thumbnail(MEDIA_SIZE)
        media_item = cls()
        image_path = instance_path / "database" / "images" / media_item.file_path
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(image_path)

        return media_item

    @property
    def file_path(self):
        """Return a “computed column”, that derives a file path from the id."""
        self_id = str(self.id)
        return pathlib.Path(f"{self_id[:1]}/{self_id[:2]}/{self_id}.webp")

    # TODO: - cascade delete from comment
    #       - delete image file when dropping database item
