#!/usr/bin/env python3


"""Return map-related resources, some static, some rendered templates."""

import mimetypes
import pathlib

import flask
import jinja2.exceptions
import werkzeug.exceptions

__all__ = [
    "Maps",
]


class Maps(flask.Blueprint):
    """Provide a blueprint for radkummerkasten front page."""

    _NAME = "maps"
    _IMPORT_NAME = __name__
    _kwargs = {
        "url_prefix": "/maps",
        "template_folder": "templates",
    }

    def __init__(self, application, *args, **kwargs):
        """Provide a blueprint for map-related assets."""
        kwargs = kwargs or {}
        kwargs.update(self._kwargs)
        super().__init__(self._NAME, self._IMPORT_NAME, *args, **kwargs)

        self.configuration = application.config

        self.add_url_rule(
            "/<path:path>",
            view_func=self.asset,
            methods=("GET",),
        )

    def asset(self, path):
        """Find a static or template file."""
        try:
            response = flask.send_from_directory(
                pathlib.Path(self.root_path) / "static",
                path,
            )
        except werkzeug.exceptions.NotFound:
            try:
                response = flask.Response(
                    flask.render_template(f"{self._NAME}/{path}.jinja"),
                    mimetype=mimetypes.guess_type(path)[0],
                )
            except jinja2.exceptions.TemplateNotFound:
                response = (flask.jsonify(error=f"{path} not found."), 404)
            except werkzeug.routing.exceptions.BuildError:
                response = (flask.jsonify(error=f"Internal server error for {path}."), 500)
        return response
