import pytest

from config import settings

OWN_ENDPOINT = "vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb"


def set_cookie_header(response) -> str:
    return response.headers["set-cookie"].lower()


def test_put_session_sets_httponly_cookie(client):
    response = client.put("/session", headers={"authorization": "Bearer valid"})
    assert response.status_code == 204
    cookie = set_cookie_header(response)
    assert cookie.startswith(f"{settings.SESSION_COOKIE_NAME}=valid")
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert f"path={settings.SESSION_COOKIE_PATH}" in cookie


def test_put_session_is_secure_for_https(client, monkeypatch):
    monkeypatch.setattr(settings, "BASE_URL", "https://example.org")
    response = client.put(
        "/session",
        headers={"authorization": "Bearer valid", "origin": "https://example.org"},
    )
    assert response.status_code == 204
    assert "secure" in set_cookie_header(response)


def test_put_session_requires_token(client):
    response = client.put("/session")
    assert response.status_code == 401
    assert "set-cookie" not in response.headers


def test_put_session_rejects_invalid_token(client):
    response = client.put("/session", headers={"authorization": "Bearer invalid"})
    assert response.status_code == 401
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize("method", ["put", "delete"])
def test_session_rejects_foreign_origin(client, method):
    response = getattr(client, method)(
        "/session",
        headers={"authorization": "Bearer valid", "origin": "https://evil.example"},
    )
    assert response.status_code == 403
    assert "set-cookie" not in response.headers


def test_delete_session_clears_cookie(client):
    response = client.delete("/session")
    assert response.status_code == 204
    cookie = set_cookie_header(response)
    assert cookie.startswith(f'{settings.SESSION_COOKIE_NAME}=""')
    assert "max-age=0" in cookie


def test_cookie_is_forwarded_to_internal_frost(
    client, frost_requests, frost_internal_requests
):
    client.cookies.set(settings.SESSION_COOKIE_NAME, "valid")
    response = client.get(f"/{OWN_ENDPOINT}/v1.1/Things")
    assert response.status_code == 200
    assert frost_requests == []
    assert len(frost_internal_requests) == 1
    # neither the cookie nor the token reach FROST
    assert "cookie" not in frost_internal_requests[0].headers
    assert "authorization" not in frost_internal_requests[0].headers


def test_internal_response_is_not_cacheable(client):
    client.cookies.set(settings.SESSION_COOKIE_NAME, "valid")
    response = client.get(f"/{OWN_ENDPOINT}/v1.1")
    assert response.headers["cache-control"] == "private, no-store"
    assert "cookie" in response.headers["vary"].lower()


def test_invalid_cookie_is_forwarded_to_public_frost(
    client, frost_requests, frost_internal_requests
):
    client.cookies.set(settings.SESSION_COOKIE_NAME, "expired")
    client.get(f"/{OWN_ENDPOINT}/v1.1")
    assert frost_internal_requests == []
    assert len(frost_requests) == 1


def test_header_takes_precedence_over_cookie(
    client, frost_requests, frost_internal_requests
):
    client.cookies.set(settings.SESSION_COOKIE_NAME, "valid")
    client.get(f"/{OWN_ENDPOINT}/v1.1", headers={"authorization": "Bearer invalid"})
    assert frost_internal_requests == []
    assert len(frost_requests) == 1


def test_session_cookie_ends_with_browser_session(client):
    response = client.put("/session", headers={"authorization": "Bearer valid"})
    cookie = set_cookie_header(response)
    assert "max-age" not in cookie
    assert "expires" not in cookie
