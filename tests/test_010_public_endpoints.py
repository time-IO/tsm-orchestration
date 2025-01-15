import os

import requests
import pytest
from environment import LOCAL


# Base URL of the Django app running in Docker
@pytest.fixture(scope="module")
def base_url():
    if LOCAL:
        return "http://localhost"
    else:
        return "https://tsm.intranet.ufz.de"


@pytest.mark.parametrize(
    "path,redirect",
    [
        ("", "/"),  # http://localhost -> http://localhost/
        ("/frontend", "/frontend/login/?next=/frontend/"),
        ("/frontend/tsm", "/frontend/login/?next=/frontend/tsm"),
        ("/visualization", "/visualization/login"),
        ("/visualization/login", "/visualization/login"),
        ("/object-storage", "/object-storage/"),
        ("/object-storage/login", "/object-storage/login"),
        ("/sta", "/sta/"),
    ],
)
def test_timeio_links(base_url, path, redirect):
    url = f"{base_url}{path}"
    expected = f"{base_url}{redirect}"
    # Get the login page to retrieve the CSRF token
    page = requests.get(url)
    assert page.status_code == 200
    assert page.url == expected
