#!/usr/bin/env python


"""Test the /tiles endpoint."""

import json

import google.protobuf.json_format
import pytest
import vt2pbf


class TestTiles:
    """Test the /tiles endpoint."""

    @staticmethod
    def decode_vector_tile(tile):
        """Decode the keys/values in a vector tile."""
        if "layers" in tile:
            for i in range(len(tile["layers"])):
                keys = dict(enumerate(tile["layers"][i]["keys"]))
                values = {
                    k: list(v.values())[i]
                    for k, v in dict(enumerate(tile["layers"][i]["values"])).items()
                }
                for j in range(len(tile["layers"][i]["features"])):
                    tile["layers"][i]["features"][j]["tags"] = {
                        keys[k]: values[v]
                        for k, v in dict(
                            zip(
                                tile["layers"][i]["features"][j]["tags"][::2],
                                tile["layers"][i]["features"][j]["tags"][1::2],
                            )
                        ).items()
                    }
                del tile["layers"][i]["keys"]
                del tile["layers"][i]["values"]
        return tile

    @pytest.mark.parametrize(
        ("layer", "z", "x", "y", "expected_tile", "expected_http_status"),
        [
            (
                "radlkarte",
                12,
                2232,
                1420,
                "radlkarte-12-2232-1420",
                200,
            ),
            (
                "radlkarte",
                15,
                17875,
                11361,
                "radlkarte-15-17875-11361",
                200,
            ),
            (
                "radlkarte",
                17,
                71495,
                45454,
                "radlkarte-17-71495-45454",
                200,
            ),
            (
                "radlkarte",
                9,
                279,
                177,
                "radlkarte-9-279-177",
                200,
            ),
            (
                "radlkarte",
                15,
                25485,
                3673,
                "radlkarte-15-25485-3673",
                200,
            ),
            (
                "non-existing",
                12,
                345,
                678,
                "non-existing-12-345-678",
                404,
            ),
        ],
        indirect=["expected_tile"],
    )
    def test_tile_by_index(
        self, client, layer, z, x, y, expected_tile, expected_http_status
    ):
        """Test retrieving one tile by index."""
        response = client.get(f"/tiles/{layer}/{z}/{x}/{y}")
        assert response.status_code == expected_http_status

        if response.status_code == 200:
            tile = self.decode_vector_tile(
                json.loads(
                    google.protobuf.json_format.MessageToJson(
                        vt2pbf.parse_from_string(response.get_data()).tile_pbf
                    )
                )
            )
            assert tile == expected_tile

    @pytest.mark.parametrize(
        ("layer", "expected_tilejson", "expected_http_status"),
        [
            (
                "radlkarte",
                "radlkarte",
                200,
            ),
            (
                "non-existing",
                "non-existing",
                404,
            ),
        ],
        indirect=["expected_tilejson"],
    )
    def test_tilejson(self, client, layer, expected_tilejson, expected_http_status):
        """Test retrieving the tilejson metadata."""
        response = client.get(f"/tiles/{layer}")
        assert response.status_code == expected_http_status
        assert response.text == expected_tilejson

    def test_without_tile_layers(self, application_with_empty_config):
        """Test retrieving a tile for a missing layer."""
        client = application_with_empty_config.test_client()
        response = client.get("/tiles/layer/12/345/678")
        assert response.status_code == 404

    def test_tile_layer_with_path(self, tile_layer_file):
        """Test the tile layer from outside a request context."""
        from radkummerkasten.core import TileLayer

        _ = TileLayer(tile_layer_file, tile_layer_file.stem)
