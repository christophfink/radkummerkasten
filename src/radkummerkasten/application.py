#!/usr/bin/env python3


"""The application object for radkummerkasten."""

import pathlib

from . import api, auth, factory, frontend, maps, tiles
from .database import Database
from .utilities.mail import Mail

__all__ = [
    "create_app",
]


__MODULE__ = __name__.split(".", maxsplit=1)[0]

DEFAULT_INSTANCE_PATH = (pathlib.Path.cwd() / "instance").absolute()


def create_app(instance_path=DEFAULT_INSTANCE_PATH):
    """Create a new radkummerkasten application."""
    application = factory.create_app(
        __MODULE__,
        instance_path=instance_path,
    )

    database = Database()
    database.init_app(application)

    mail = Mail()
    mail.init_app(application)

    application.register_blueprint(frontend.Radkummerkasten(application))
    application.register_blueprint(tiles.Tiles(application))
    application.register_blueprint(api.Address(application))
    application.register_blueprint(api.Issues(application))
    application.register_blueprint(auth.Auth(application))
    application.register_blueprint(maps.Maps(application))

    return application
