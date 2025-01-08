import os
from unittest import mock

import pytest
import dotenv as dotenv_lib

dc_environ = {}
dotenvs = []


# Here we add the '--env' option to pytest.
# we need to handle dotenv files manually, because some
# variables cannot be set by sourcing the file (e.g. UID).
# This is because the dotenv files are intended to be used
# with docker-compose and not on the host system.
def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--env",
        dest="file",
        action="append",
        required=True,
        help="Use environment variables from `FILE` (mandatory, multi-allowed)",
    )


# Process --env options
# Store variables from dotenv files in a global
# environment, for later use (see environment.py)
def pytest_configure(config: pytest.Config):
    files = config.getoption("file", []) or []
    for file in files:
        dotenvs.append(file)
        dc_environ.update(dotenv_lib.dotenv_values(file))
