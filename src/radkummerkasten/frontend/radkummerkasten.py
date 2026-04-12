#!/usr/bin/env python3


"""Return the single-page radkummerkasten front page."""

import flask

from ..core import UserManager

__all__ = [
    "Radkummerkasten",
]


class Radkummerkasten(flask.Blueprint):
    """Provide a blueprint for radkummerkasten front page."""

    _NAME = "radkummerkasten"
    _IMPORT_NAME = __name__
    _kwargs = {
        "url_prefix": "/",
    }

    def __init__(self, application, *args, **kwargs):
        """Provide a blueprint for radkummerkasten lookup."""
        kwargs = kwargs or {}
        kwargs.update(self._kwargs)
        super().__init__(self._NAME, self._IMPORT_NAME, *args, **kwargs)

        self.configuration = application.config

        self.user_manager = UserManager()

        self.add_url_rule(
            "/",
            view_func=self.radkummerkasten,
            methods=("GET",),
        )
        self.add_url_rule(
            "/favicon.ico",
            endpoint="favicon",
            redirect_to=application.url_for("static", filename="images/favicon.ico"),
        )

    def radkummerkasten(self):
        """Return the single-page radkummerkasten front page."""
        # mail = flask.current_app.extensions["mail"]
        # mail.send_message(
        #     subject="Test",
        #     recipients=[
        #         "christoph.fink@christophfink.com",
        #         "christoph.fink@univie.ac.at",
        #         "christoph.fink@gmail.com",
        #     ],
        #     body=(
        #         "This is a test e-mail."
        #         "\n\n"
        #         "i’m just trying out how flask_mail works (and whether it does)."
        #     ),
        # )
        user = self.user_manager.current_user
        return flask.render_template("map.html.jinja", user=user)
