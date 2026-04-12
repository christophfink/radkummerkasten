#!/usr/bin/env python3


"""Update the GeoPackage copy of the issues tables."""

import math
import pathlib
import tempfile

import filelock
import flask
import geopandas
import numpy
import pandas
import sklearn.cluster
from sqlalchemy import select

from ..core.tile_layer import MAX_ZOOM, MIN_ZOOM
from ..database import Database
from ..database.models import (
    Issue,
)

__all__ = ["GeopackageUpdater"]


# short-hand for a quick approximate conversion between meters and degrees
EARTH_CIRCUMFERENCE_M = 2 * 6_371_000 * math.pi
M_TO_DEGREES = 360.0 / EARTH_CIRCUMFERENCE_M

# DBSCAN’s epsilon parameter, by TMS zoom level
# These values are based on a trial-and-error exploration,
# originally, the idea was to directly derive them from the tile grid side
# lengths, but that did not quite work.
# For TMS tile sizes, see https://developer.tomtom.com/map-display-api/
# documentation/tomtom-maps/zoom-levels/zoom-levels-and-tile-grid

EPSILON_BY_ZOOM_LEVEL = {
    0: math.inf,
    1: math.inf,
    2: math.inf,
    3: math.inf,
    4: math.inf,
    5: math.inf,
    6: math.inf,
    7: 120_000 * M_TO_DEGREES,
    8: 60_000 * M_TO_DEGREES,
    9: 200_000 * M_TO_DEGREES,
    10: 10_000 * M_TO_DEGREES,
    11: 4_000 * M_TO_DEGREES,
    12: 1_000 * M_TO_DEGREES,
    13: 400 * M_TO_DEGREES,
    14: 180 * M_TO_DEGREES,
    15: 4 * M_TO_DEGREES,
    16: 0,
    17: 0,
    18: 0,
    19: 0,
    20: 0,
    21: 0,
    22: 0,
}


class GeopackageUpdater:
    """Update the GeoPackage copy of the issues tables."""

    def __init__(self, application=None):
        """
        Update the GeoPackage copy of the issues tables.

        Arguments
        ---------
        application : flask.Application
            The parent flask app. If ``None``, ``flask.current_app`` at runtime

        """
        self.application = application

    @property
    def application(self):
        """Reference to the parent flask app."""
        try:
            application = self._application
        except AttributeError:
            application = None
        if application is None:
            application = flask.current_app
        return application

    @application.setter
    def application(self, application):
        self._application = application

    @property
    def database(self):
        """Retrieve a radkummerkasten.database.Database instance."""
        database = self.application.extensions[Database.EXTENSION_NAME]
        return database

    @property
    def path(self):
        """Retrieve the file path to the issues’ radkummerkasten.core.TileLayer."""
        return pathlib.Path(
            self.application.blueprints["tiles"].tile_layers["issues"].data
        )

    def cluster(self, df, eps):
        """Cluster the point coordinates in ``df`` by distance threshold."""
        df = df.copy()
        coordinates = numpy.vstack(
            df["geometry"].apply(lambda geometry: numpy.hstack(geometry.xy)).values
        )
        df["label"] = (
            sklearn.cluster.AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=eps,
                linkage="complete",
            )
            .fit(coordinates)
            .labels_
        )
        return df

    def cluster_for_zoom_level(self, df, zoom_level):
        """Cluster the point coordinates in ``df`` for a certain TMS zoom level."""
        eps = EPSILON_BY_ZOOM_LEVEL[zoom_level]
        if eps == 0:
            clusters = df.assign("num_issues", 1)
        else:
            clusters = self.cluster(df, eps)
            clusters = clusters.dissolve(
                by="label",
                aggfunc={
                    "id": lambda ids: ",".join(str(i) for i in list(ids)),
                    "num_issues": sum,
                    "symbol-sort-key": max,
                },
            ).reset_index(drop=True)

            orig_crs = clusters.crs
            clusters["geometry"] = (
                clusters["geometry"].to_crs("EPSG:3857").centroid.to_crs(orig_crs)
            )

        # clusters = clusters[["id", "num_issues", "symbol-sort-key", "geometry"]]

        return clusters

    def update_geopackage(self):
        """Update the GeoPackage copy of the issues tables."""
        data = {
            "id": [],
            "lon": [],
            "lat": [],
        }
        with self.database.session() as session:
            for id_, lon, lat in session.execute(
                select(Issue.id, Issue.lon, Issue.lat)
            ):
                data["id"].append(id_)
                data["lon"].append(lon)
                data["lat"].append(lat)

            issues = geopandas.GeoDataFrame(
                {
                    "id": pandas.Series(data["id"], dtype=str),
                    "geometry": geopandas.points_from_xy(
                        data["lon"],
                        data["lat"],
                        crs="EPSG:4326",
                    ),
                    "num_issues": pandas.Series(dtype=int),
                    "symbol-sort-key": pandas.Series(dtype=int),
                }
            )
            issues["num_issues"] = 1
            issues["symbol-sort-key"] = issues.index * -1

        if len(issues) == 0:
            with filelock.FileLock(self.path.with_suffix(f"{self.path.suffix}.lock")):
                issues.to_file(
                    self.path,
                    layer=f"z{MIN_ZOOM}-{MAX_ZOOM}",
                )
        else:
            with (
                filelock.FileLock(self.path.with_suffix(f"{self.path.suffix}.lock")),
                tempfile.TemporaryDirectory() as temporary_directory,
            ):
                temporary_geopackage = (
                    pathlib.Path(temporary_directory) / self.path.name
                )

                # save full details for MAX_ZOOM
                issues.to_file(
                    temporary_geopackage,
                    layer=f"z{MAX_ZOOM}-{MAX_ZOOM}",
                )

                # decrease zoom level until only one cluster left
                for zoom_level in range(MAX_ZOOM - 1, MIN_ZOOM - 1, -1):
                    clusters = self.cluster_for_zoom_level(issues, zoom_level)
                    if len(clusters) > 1:
                        clusters.to_file(
                            temporary_geopackage,
                            layer=f"z{zoom_level}-{zoom_level}",
                        )
                    else:
                        clusters.to_file(
                            temporary_geopackage,
                            layer=f"z{MIN_ZOOM}-{zoom_level}",
                        )
                        break

                temporary_geopackage.move(self.path)
