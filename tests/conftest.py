import pytest
import dotenv


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


# Merge files (--env FILE1 --env FILE2 ...) into os.environ
def pytest_configure(config: pytest.Config):
    files = config.getoption("file", []) or []
    for file in files:
        dotenv.load_dotenv(file, override=True)
