import os

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

# CORS must not allow credentials.
# Otherwise, any website could read internal data of logged-in users.
SESSION_COOKIE_NAME = "sta_session"
FOREIGN_ORIGIN = "https://evil.example"


@pytest.fixture
def sta_url():
    url = os.environ.get("STA_PROXY_URL")
    if not url:
        pytest.fail("STA_PROXY_URL not set")
    return url.rstrip("/") + "/endpoints/"


def assert_no_credentialed_cors(response: requests.Response) -> None:
    assert response.headers.get("Access-Control-Allow-Origin") == "*"
    assert "Access-Control-Allow-Credentials" not in response.headers


def test_sta_cors_does_not_allow_credentials(sta_url):
    response = requests.get(
        sta_url,
        headers={"Origin": FOREIGN_ORIGIN},
        cookies={SESSION_COOKIE_NAME: "invalid"},
        timeout=5,
    )
    response.raise_for_status()
    assert_no_credentialed_cors(response)


def test_sta_cors_preflight_does_not_allow_credentials(sta_url):
    response = requests.options(
        sta_url,
        headers={
            "Origin": FOREIGN_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
        timeout=5,
    )
    assert response.status_code == 204
    assert_no_credentialed_cors(response)
