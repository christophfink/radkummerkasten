#!/usr/bin/env python3


"""Provide authentication endpoints."""

import flask

from ..core import (
    PasswordlessAuthentication,
    UserManager,
)
from ..forms import LoginForm
from ..utilities.decorators import local_referer_only

__all__ = [
    "Auth",
]


class Auth(flask.Blueprint):
    """Provide a blueprint for address lookup."""

    _NAME = "auth"
    _IMPORT_NAME = __name__
    _kwargs = {
        "url_prefix": "/auth",
    }

    def __init__(self, application, *args, **kwargs):
        """Provide a blueprint for address lookup."""
        kwargs = kwargs or {}
        kwargs.update(self._kwargs)
        super().__init__(self._NAME, self._IMPORT_NAME, *args, **kwargs)

        self.configuration = application.config

        self.authentication_backend = PasswordlessAuthentication(
            # self.configuration.get("SECRET_KEY"),
        )
        self.user_manager = UserManager()

        self.add_url_rule(
            "/login",
            view_func=self.get_login,
            methods=("GET",),
        )
        self.add_url_rule(
            "/login",
            view_func=self.post_login,
            methods=("POST",),
        )
        self.add_url_rule(
            "/<string:token>",
            view_func=self.verify,
            methods=("GET",),
        )

    def get_login(self):
        """Show login form."""
        form = LoginForm(flask.request.form)
        return flask.render_template("login.html.jinja", form=form)

    @local_referer_only
    def post_login(self):
        """Read login form input, send auth email."""
        form = LoginForm(flask.request.form)
        if form.validate():
            self.authentication_backend.send_magic_link(form.email_address.data)
        else:
            print("not valid?")
            print(form.errors)
            # self.authentication_backend.send_magic_link(form.email_address.data)
        return flask.render_template("magic_link_sent.html.jinja")

    def verify(self, token):
        """Verify magic link token."""
        token_valid = self.authentication_backend.verify_magic_link(token)
        if token_valid:
            user = self.user_manager.current_user
            print(user, user.details_confirmed)
            if user.details_confirmed is None:
                # TODO: redirect to profile details form
                return flask.redirect(
                    flask.url_for(
                        "radkummerkasten.radkummerkasten",
                        code=303,
                    )
                )
        return flask.redirect(
            flask.url_for(
                "radkummerkasten.radkummerkasten",
                code=303,
            )
        )
