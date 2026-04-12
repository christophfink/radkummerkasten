#!/usr/bin/env python


"""Test the /maps endpoint."""

import pytest


class TestMaps:
    """Test the /maps endpoint."""

    @pytest.mark.parametrize(
        ("path", "expected_status_code"),
        [
            ("combined-root.json", 200),
            ("basemapv-bmapv-3857.json", 200),
            ("does-not-exist", 404),
        ],
    )
    def test_maps(self, client, path, expected_status_code):
        """Test the /maps endpoint."""
        response = client.get(f"/maps/{path}")
        assert response.status_code == expected_status_code
