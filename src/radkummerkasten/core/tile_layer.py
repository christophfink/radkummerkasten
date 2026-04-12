#!/usr/bin/env python3


"""Compute vector tiles of a dataset for a given zoom level and tile index."""

import functools
import re
import warnings

import flask
import geopandas
import mercantile
import pyogrio
import shapely
import vt2pbf

from ..utilities import BytesCache

__all__ = [
    "TileLayer",
]


MIN_ZOOM = 7
MAX_ZOOM = 17
TILE_WIDTH = TILE_HEIGHT = 4096
TILE_BUFFER = 64


class TileLayer:
    """Compute vector tiles of a dataset for a zoom level and tile index."""

    EMPTY_TILE = vt2pbf.Tile().serialize_to_bytestring()

    def __init__(self, data, layer_name):
        """
        Compute vector tiles of one of more datasets.

        Arguments
        ---------
        data : pathlib.Path
            the layer to serve, in a format readable by geopandas.read_file,
            preferrably containing a spatial index
        layer_name : str
            the name of this layer (included, e.g., in the tilejson metadata)
        """
        self.data = data
        self.layer_name = layer_name
        self.cache = BytesCache(layer_name)

    @functools.cached_property
    def bounds(self):
        """The geographic bounds of the layer."""
        bounds = [
            float(coordinate)
            for coordinate in pyogrio.read_info(self.data, layer=0)["total_bounds"]
        ]
        return bounds

    @functools.cached_property
    def fields(self):
        """The attribute fields of the layer."""
        data = geopandas.read_file(self.data, layer=0)
        fields = [
            str(column_name)
            for column_name in data.columns
            if column_name != "geometry"
        ]
        return fields

    @functools.cached_property
    def layers(self):
        """Layers contained in the data file."""
        layers = list(geopandas.list_layers(self.data)["name"])
        return layers

    @functools.cached_property
    def layers_by_zoom_level(self):
        """Enumerate ``self.data``’s layers by zoom level."""
        layers_by_zoom_level = {}
        layers = []

        zoom_layer_re = re.compile("^z(?P<min>[0-9]+)-(?P<max>[0-9]+)$")

        for layer in self.layers:
            try:
                min_zoom, max_zoom = zoom_layer_re.match(layer).groups()
                layers.append(
                    {
                        "name": layer,
                        "min_zoom": int(min_zoom),
                        "max_zoom": int(max_zoom),
                    }
                )
            except AttributeError:  # 'NoneType' object has no attribute 'groups'
                pass
        if not layers:
            if len(self.layers) > 1:
                warnings.warn(
                    f"Found multiple layers in {self.data}, "
                    "but none match layer name template (e.g., ’z0-24’).",
                    RuntimeWarning,
                    stacklevel=1,
                )
            layers = [
                {
                    "name": self.layers[0],
                    "min_zoom": MIN_ZOOM,
                    "max_zoom": MAX_ZOOM,
                }
            ]
        else:
            layers = sorted(layers, key=lambda layer: layer["min_zoom"])

            layers[0]["min_zoom"] = MIN_ZOOM
            layers[-1]["max_zoom"] = MAX_ZOOM

            overlapping = any(
                (layers[i]["max_zoom"] > layers[i + 1]["min_zoom"])
                for i in range(len(layers) - 1)
            )
            if overlapping:
                warnings.warn(
                    f"Overlapping zoom level layers found in {self.data}, "
                    "results may vary.",
                    RuntimeWarning,
                    stacklevel=1,
                )

        for layer in layers:
            for zoom_level in range(layer["min_zoom"], layer["max_zoom"] + 1):
                layers_by_zoom_level[zoom_level] = layer["name"]

        return layers_by_zoom_level

    def read_file_at_zoom_level(self, zoom_level, **kwargs):
        """
        Read the appropriate layer of multi-layer GPKG.

        zoom_level : int
            the TMS/vector tile zoom level to read data for
        **kwargs
            passed through to ``geopandas.read_file()``

        """
        try:
            del kwargs["layer"]
        except KeyError:
            pass

        return geopandas.read_file(
            self.data,
            layer=self.layers_by_zoom_level[zoom_level],
            **kwargs,
        )

    def empty_cache(self):
        """Delete the entire content of the cache."""
        self.cache.empty()

    def expire_cache_for_lon_lat(self, lon, lat):
        """
        Delete the cached tile that covers/contains a point.

        Arguments
        ---------
        lon : float
        lat : float
            coordinates of a point
        """
        tile = mercantile.tile(lon, lat, MAX_ZOOM)
        while tile is not None:
            self.cache.expire(f"{tile.z}/{tile.x}/{tile.y}", now=True)
            tile = mercantile.parent(tile)

    def tile(self, z, x, y):
        """
        Retrieve the vector tile at tile index `x`, `y` for zoom level `z`.

        Arguments
        ---------
        x, y, z : int
            coordinates and zoom level of the tile requested
        """
        try:
            tile = self.cache[f"{z}/{x}/{y}"]
        except KeyError:
            bounds = mercantile.bounds(mercantile.Tile(x, y, z))
            left, bottom, right, top = bounds
            width = right - left
            height = top - bottom

            # Add a buffer that would be 64 units (of 4096 width) in the output pbf
            mask = shapely.box(*bounds).buffer(width / (TILE_HEIGHT / TILE_BUFFER))

            features = self.read_file_at_zoom_level(z, mask=mask).clip(mask, sort=True)

            if len(features) > 0:
                # make sure we don’t have multigeometries
                features = features.explode()

                # transform to tile coordinate space
                transform_to_tile_coordinate_space = functools.partial(
                    self._transform_to_tile_coordinate_space,
                    origin=(left, bottom),
                    ratio=((TILE_WIDTH / width), (TILE_HEIGHT / height)),
                )
                features["geometry"] = shapely.transform(
                    features["geometry"].force_2d(),
                    transform_to_tile_coordinate_space,
                )

                features = features.reset_index(drop=True)
                features["id_"] = features.index

                features = features.apply(self._convert_feature, axis=1).to_list()

                tile = vt2pbf.service.tile.Tile()
                tile.add_layer(self.layer_name, features)
                tile = tile.serialize_to_bytestring()

            else:
                tile = self.EMPTY_TILE

            self.cache[f"{z}/{x}/{y}"] = tile

        return tile

    @property
    def tilejson(self):
        """Return metadata for this tile layer."""
        # https://github.com/mapbox/tilejson-spec/tree/master/3.0.0
        tilejson = {
            "tilejson": "3.0.0",
            "name": self.layer_name,
            "description": self.layer_name,
            "tiles": [self.tile_url],
            "bounds": self.bounds,
            "vector_layers": [
                {
                    "id": self.layer_name,
                    "fields": {field: field for field in self.fields},
                }
            ],
        }
        return tilejson

    @property
    def tile_url(self):
        """Return the URL template for fetching tiles."""
        tile_layer_url = flask.url_for(
            "tiles.tilejson",
            tile_layer=self.layer_name,
            _external=True,
        )
        return f"{tile_layer_url}" "/{z}/{x}/{y}"

    @staticmethod
    def _transform_to_tile_coordinate_space(
        coordinates,
        origin,
        ratio,
    ):
        coordinates = coordinates.swapaxes(0, 1)
        coordinates[0] = (coordinates[0] - origin[0]) * ratio[0]
        coordinates[1] = TILE_HEIGHT - ((coordinates[1] - origin[1]) * ratio[1])
        coordinates = coordinates.swapaxes(0, 1)
        return coordinates

    @staticmethod
    def _convert_feature(row):
        row = row.to_dict()
        id_ = row.pop("id_")
        geometry = row.pop("geometry")

        geometry_type = 0  # UNKNOWN
        coordinates = []
        if geometry.geom_type == "Point":
            geometry_type = 1
            coordinates = [
                [round(geometry.x), round(geometry.y)],
            ]
        elif geometry.geom_type == "LineString":
            geometry_type = 2
            coordinates = [
                [[round(x), round(y)] for x, y in geometry.coords],
            ]
        elif geometry.geom_type == "Polygon":
            coordinates = [
                [
                    [[round(x), round(y)] for x, y in part.coords]
                    for part in [geometry.exterior] + list(geometry.interiors)
                ],
            ]
            geometry_type = 3

        feature = {
            "id": id_,
            "geometry": coordinates,
            "tags": row,
            "type": geometry_type,
        }

        return feature
