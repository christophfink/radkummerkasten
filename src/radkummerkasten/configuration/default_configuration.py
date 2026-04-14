#!/usr/bin/env python3


"""Default configuration options."""

import datetime


class BaseConfiguration:
    """Base configuration, inherited by all other config objects."""


class DefaultConfiguration(BaseConfiguration):
    """Default configuration."""
    # pylint: disable=too-few-public-methods

    PERMANENT_SESSION_LIFETIME = datetime.timedelta(weeks=26)
    ADDITIONAL_TILE_LAYERS = {}
    STATIC_FOLDER = None
    TEMPLATE_FOLDER = None
    SERVER_NAME = "localhost"
