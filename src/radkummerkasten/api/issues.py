#!/usr/bin/env python3


"""Look up the closest street issue for a pair of coordinates."""

import flask

from ..core import GeopackageUpdater
from ..database import Database
from ..database.models import (  # IssueType,; User,
    Issue,
)
from ..utilities.decorators import local_referer_only

__all__ = [
    "Issues",
]


PACKAGE = __package__.split(".", maxsplit=1)[0]


class Issues(flask.Blueprint):
    """Provide a blueprint for issue lookup."""

    _NAME = "issue"
    _IMPORT_NAME = __name__
    _kwargs = {
        "url_prefix": "/api/issue",
    }

    def __init__(self, application, *args, **kwargs):
        """Provide a blueprint for issue lookup."""
        kwargs = kwargs or {}
        kwargs.update(self._kwargs)
        super().__init__(self._NAME, self._IMPORT_NAME, *args, **kwargs)

        self.application = application
        self.configuration = application.config

        self.update_geopackage()

        self.add_url_rule(
            "/<uuid:issue_id>",
            view_func=self.get_issue,
            methods=("GET",),
        )
        self.add_url_rule(
            "/<uuid:issue_id>",
            view_func=self.patch_issue,
            methods=("PATCH",),
        )
        self.add_url_rule(
            "/",
            view_func=self.post_issue,
            methods=("POST",),
        )

    @property
    def database(self):
        """Retrieve a radkummerkasten.database.Database instance."""
        database = self.application.extensions[Database.EXTENSION_NAME]
        return database

    def expire_tile_layer(self, lon=None, lat=None):
        """Expire the tile layer, possibly limited to one location."""
        if lon is None and lat is not None or lon is not None and lat is None:
            raise ValueError("Set `lon` and `lat`, or neither.")
        if lon is None and lat is None:
            self.tile_layer.empty_cache()
        else:
            self.tile_layer.expire_cache_for_lon_lat(lon, lat)

    @local_referer_only
    def get_issue(self, issue_id):
        """Retrieve the details for one issue."""
        with self.database.session() as session:
            issue = session.get(Issue, issue_id)
            if issue is None:
                issue = {"error": "Issue not found"}
            else:
                issue = {
                    "id": issue.id,
                    "issue_type": issue.issue_type.value,
                    "lon": issue.lon,
                    "lat": issue.lat,
                    "created": f"{issue.created:%Y-%m-%d %H:%M:%S}",
                    "updated": f"{issue.updated:%Y-%m-%d %H:%M:%S}",
                    "comments": [
                        {
                            "id": comment.id,
                            "title": comment.title,
                            "text": comment.text,
                            "created": f"{comment.created:%Y-%m-%d %H:%M:%S}",
                            "updated": f"{comment.updated:%Y-%m-%d %H:%M:%S}",
                            "user": {
                                "id": comment.user.id,
                                "first_name": comment.user.first_name,
                                "last_name": comment.user.last_name,
                                "email_address": comment.user.email_address,
                                # TODO: anonymise when not admin user
                            },
                            "media": [{"id": media.id} for media in comment.media],
                        }
                        for comment in issue.comments
                    ],
                    "address": {
                        "street": issue.address.street,
                        "housenumber": issue.address.housenumber,
                        "postcode": issue.address.postcode,
                        "municipality": issue.address.municipality,
                    },
                }
        return flask.jsonify(issue)

    @local_referer_only
    def patch_issue(self, issue_id):
        """Update an issue."""
        # TODO: implement this, using Flask-WTF to validate inputs

        # if admin and user_id set -> use that user_id
        # otherwise: use current session user id

        # with self.database.session.begin() as session:
        #     issue = session.get(Issue, issue_id)
        #     session.commit()
        lon = None
        lat = None

        self.update_geopackage()
        self.expire_tile_layer(lon, lat)

    @local_referer_only
    def post_issue(self):
        """Create a new issue."""
        # TODO: implement this, using Flask-WTF to validate inputs

        # with self.database.session.begin() as session:
        #     issue = session.get(Issue, issue_id)
        #     session.commit()
        lon = None
        lat = None

        self.update_geopackage()
        self.expire_tile_layer(lon, lat)

    @property
    def tile_layer(self):
        """Retrieve the radkummerkasten.core.TileLayer for these issues."""
        return self.application.blueprints["tiles"].tile_layers["issues"]

    def update_geopackage(self):
        """Update the geopackage copy of the issue table."""
        GeopackageUpdater(self.application).update_geopackage()
