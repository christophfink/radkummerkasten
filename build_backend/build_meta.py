#!/usr/bin/env python3


"""
A custom build backend that also compiles SASS and ECMA-script.

This build backend is a thin wrapper around the default setuptools.build_meta
backend. It compiles SASS source files to CSS and transpiles and concatenates
ECMA script files into one common JavaScript file. This build backend works on
Python >=3.11 and implements a PEP517 in-tree build backend.

To configure which files are compiled and transpiled, add a section
`tools.radkummerkasten-build-backend` to `pyproject.toml` and add the options
`sass_files` and `ecmascript_files` (both lists of file paths relative to
`pyproject.toml`). The SASS files will be individually compiled to CSS files
with the same name but the extension `.min.css`. The ECMA files will be
transpiled and concatenated into one file with the name of the first file listed
and the extension `.min.js`.


Example configuration:
```
[tools.radkummerkasten-build-backend]
sass_files = ["src/radkummerkasten/frontend/static/radkummerkasten.sass"]
ecmascript_files = ["src/radkummerkasten/frontend/static/radkummerkasten.js"]
```

"""

import functools
import os
import pathlib

try:
    import tomllib
except ModuleNotFoundError:  # Python <3.11
    import tomli as tomllib

import setuptools.build_meta
from setuptools.build_meta import *  # noqa: F401, F403

BUILD_REQUIREMENTS = [
    "libsass",
    "nodejs-bin@git+https://github.com/christophfink/nodejs-pypi.git",
]


class WorkingDirectory:
    """Context manager to change working directory."""

    def __init__(self, working_directory):
        """Context manager to change working directory."""
        self._working_directory = pathlib.Path(working_directory)
        self._original_working_directory = None

    def __enter__(self):
        """Continue working in a new directory."""
        self._original_working_directory = pathlib.Path.cwd()
        os.chdir(self._working_directory)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Return to the original working directory."""
        os.chdir(self._original_working_directory)


@functools.cache
def _assert_babeljs_available():
    import nodejs

    nodejs.npm.call(
        "install",
        "@babel/core",
        "@babel/cli",
        "babel-preset-minify",
    )
    return True


@functools.cache
def _compile_maplibre_gl_js():
    import nodejs

    with WorkingDirectory("vendor/maplibre-gl-js"):
        nodejs.npm.call("ci")
        nodejs.npm.call("run", "build-dist")


def _compile_sass_file(input_filename):
    import sass

    output_filename = input_filename.with_suffix(".min.css")
    with output_filename.open("w") as f:
        f.write(sass.compile(filename=f"{input_filename}", output_style="compressed"))
    return output_filename


def _compile_ecmascript_file(input_filenames):
    import nodejs

    _assert_babeljs_available()
    output_filename = input_filenames[0].parent / "radkummerkasten.min.js"
    nodejs.npx.run(
        ["babel"]
        + [f"{input_filename}" for input_filename in input_filenames]
        + ["--presets", "minify"]
        + ["--out-file", f"{output_filename}"]
    )
    return output_filename


@functools.cache
def _configuration():
    with (pathlib.Path.cwd() / "pyproject.toml").open("rb") as f:
        configuration = tomllib.load(f)["tools"]["radkummerkasten-build-backend"]
    return configuration


def _find_ecmascript_files():
    try:
        ecmascript_files = [
            pathlib.Path(ecmascript_file)
            for ecmascript_file in _configuration()["ecmascript_files"]
        ]
    except KeyError:
        ecmascript_files = []
    return ecmascript_files


def _find_sass_files():
    try:
        sass_files = [
            pathlib.Path(sass_file) for sass_file in _configuration()["sass_files"]
        ]
    except KeyError:
        sass_files = []
    return sass_files


def build_ecmascript(f):
    """Decorate a function to compile ECMAScript->JavaScript before function."""

    def wrapper(*args, **kwargs):
        compiled_ecmascript_file = _compile_ecmascript_file(_find_ecmascript_files())
        results = f(*args, **kwargs)
        compiled_ecmascript_file.unlink(missing_ok=True)
        return results

    return wrapper


def build_maplibre_gl_js(f):
    """Decorate a function to compile maplibre-gl-js before function."""

    def wrapper(*args, **kwargs):
        _compile_maplibre_gl_js()
        results = f(*args, **kwargs)
        return results

    return wrapper


def build_sass(f):
    """Decorate a function to compile SASS->CSS before function."""

    def wrapper(*args, **kwargs):
        compiled_sass_files = [
            _compile_sass_file(sass_file) for sass_file in _find_sass_files()
        ]
        results = f(*args, **kwargs)
        [
            compiled_sass_file.unlink(missing_ok=True)
            for compiled_sass_file in compiled_sass_files
        ]
        return results

    return wrapper


@build_ecmascript
@build_sass
def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    """Override setuptools.build_meta to also compile SASS and JS files."""
    return setuptools.build_meta.build_editable(
        wheel_directory, config_settings, metadata_directory
    )


@build_ecmascript
@build_sass
@build_maplibre_gl_js
def build_sdist(sdist_directory, config_settings=None):
    """Override setuptools.build_meta also compile SASS and JS files."""
    return setuptools.build_meta.build_sdist(sdist_directory, config_settings)


@build_ecmascript
@build_sass
@build_maplibre_gl_js
def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """Override setuptools.build_meta to also compile SASS and JS files."""
    return setuptools.build_meta.build_wheel(
        wheel_directory, config_settings, metadata_directory
    )


def get_requires_for_build_editable(config_settings=None):
    """Override setuptools.build_meta to install libsass and babeljs."""
    return BUILD_REQUIREMENTS


def get_requires_for_build_sdist(config_settings=None):
    """Override setuptools.build_meta to install libsass and babeljs."""
    return BUILD_REQUIREMENTS


def get_requires_for_build_wheel(config_settings=None):
    """Override setuptools.build_meta to install libsass and babeljs."""
    return BUILD_REQUIREMENTS
