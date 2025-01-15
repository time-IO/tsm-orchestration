import os

import requests
import pytest
from bs4 import BeautifulSoup

from environment import LOCAL


@pytest.fixture(scope="module")
def session():
    """Session to maintain cookies"""
    return requests.Session()


# Base URL of the Django app running in Docker
@pytest.fixture(scope="module")
def base_url():
    if LOCAL:
        return "http://localhost/frontend"
    else:
        return "https://tsm.intranet.ufz.de/frontend"


@pytest.fixture(scope="module")
def login_data():
    if LOCAL:
        return {
            "username": "DemoUser",
            "password": "DemoUser",
        }
    else:
        return {
            "username": os.environ["FRONTEND_USER"],
            "password": os.environ["FRONTEND_PASS"],
        }


@pytest.fixture(scope="module")
def user_name():
    if LOCAL:
        return "John"
    else:
        return "TestSuite"


def test_frontend_login(session, base_url, login_data, user_name):

    # Get the login page to retrieve the CSRF token
    login_page = session.get(base_url)
    assert login_page.status_code == 200

    # Parse the HTML to find the CSRF token
    soup = BeautifulSoup(login_page.text, "html.parser")
    csrf_token = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]
    login_data["csrfmiddlewaretoken"] = csrf_token

    login_url = login_page.url
    assert login_page.url == f"{base_url}/login/?next=/frontend/"

    # Do the actual login
    overview_page = session.post(
        login_url, data=login_data, headers={"Referer": login_url}
    )
    soup = BeautifulSoup(overview_page.text, "html.parser")
    assert overview_page.status_code == 200
    assert soup.body.i.text == f"Logged in as {user_name}"
