#!/usr/bin/env python3


"""Common fixtures and settings for testing radkummerkasten."""

import json
import os
import pathlib
import shutil
import tempfile

import pytest

import radkummerkasten

from .local_server import LocalServer

DATA_DIRECTORY = (pathlib.Path(__file__).parent / "data").absolute()
INSTANCE_DIRECTORY = (pathlib.Path(__file__).parent / "instance").absolute()

TILE_LAYER_FILE = INSTANCE_DIRECTORY / "data" / "radlkarte-wien.geojson"
PHOTO_PATH = DATA_DIRECTORY / "lorry-across-bikelane.jpg"


@pytest.fixture(scope="session")
def application(instance_directory):
    """Start a flask application."""
    # delete instance database(s) to provide a clean slate for testing
    try:
        (INSTANCE_DIRECTORY / "database" / "radkummerkasten.sqlite").unlink()
    except FileNotFoundError:
        pass

    os.environ["TESTING"] = "TRUE"
    application = radkummerkasten.create_app(instance_path=instance_directory)
    del os.environ["TESTING"]
    yield application


@pytest.fixture(scope="session")
def application_with_empty_config():
    """Start a flask application."""
    with tempfile.TemporaryDirectory() as instance_path:
        os.environ["TESTING"] = "TRUE"
        application = radkummerkasten.create_app(instance_path)
        del os.environ["TESTING"]
        yield application


@pytest.fixture(scope="session")
def cache():
    """Provide and tear down a radkummerkasten.utilities.cache."""
    cache = radkummerkasten.utilities.BytesCache("test")
    yield cache
    shutil.rmtree(cache.cache_directory)


@pytest.fixture(scope="session")
def client(application):
    """Provide a client for the tests."""
    return application.test_client()


@pytest.fixture(scope="session")
def database(application):
    """Provide a database instance."""
    from radkummerkasten.database import Database

    yield application.extensions[Database.EXTENSION_NAME]


@pytest.fixture(scope="session")
def data_directory():
    """Return the path to the test data directory."""
    yield DATA_DIRECTORY


@pytest.fixture(scope="function")
def expected_tilejson(request, data_directory):
    """Read the expected content of a vector tile from disk."""
    return pathlib.Path(data_directory / f"{request.param}.tilejson").read_text()


@pytest.fixture(scope="function")
def expected_tile(request, data_directory):
    """Read the expected content of a vector tile from disk."""
    with (data_directory / f"{request.param}.json").open() as f:
        tile = json.load(f)
    return tile


@pytest.fixture(scope="session")
def instance_directory():
    """Return the path to the test instance directory."""
    yield INSTANCE_DIRECTORY


@pytest.fixture(scope="class")
def local_server_url(application):
    """Start a listening server and return the base URL."""
    with LocalServer(application) as url:
        yield url


@pytest.fixture(scope="session")
def photo_path():
    """Return the path to a test image file."""
    yield PHOTO_PATH


@pytest.fixture(scope="session")
def runner(application):
    """Provide a cli runner for the tests."""
    return application.test_cli_runner()


@pytest.fixture(scope="session")
def tile_layer_file():
    """Return the path to a test tile layer file."""
    yield TILE_LAYER_FILE


@pytest.fixture(scope="class")
def webdriver():
    """Provide a selenium/gecko webdriver."""
    try:
        import selenium.webdriver

        options = selenium.webdriver.FirefoxOptions()
        options.add_argument("--headless=new")
        driver = selenium.webdriver.Firefox(options)

        yield driver

        driver.quit()
    except ImportError:
        yield None
