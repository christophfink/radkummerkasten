#!/usr/bin/env python3


"""Define configuration options for testing radkummerkasten."""

import pathlib

_DATA_DIR = pathlib.Path(__file__).parent.resolve() / "data"


ADDITIONAL_TILE_LAYERS = {
    "radlkarte": _DATA_DIR / "radlkarte-wien.gpkg",
}

ADDRESS_LOOKUP_LAYER = _DATA_DIR / "austrian-addresses-voronoi.gpkg.zip"
