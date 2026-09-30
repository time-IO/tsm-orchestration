import asyncio

import httpx
import pytest

import services.dsm_api as dsm_api
from services.dsm_api import fetch_dsm_api
from services.permission_groups import (
    fetch_own_database_usernames,
    search_own_ingests,
)


def test_forwards_authorization_and_params(dsm_requests):
    data = asyncio.run(
        fetch_dsm_api("/ingest/", "Bearer valid", params={"name[ilike]": "%x%"})
    )

    assert data == {"items": [{"id": 10, "permission_group_id": 1}]}
    request = dsm_requests[-1]
    assert request.headers["authorization"] == "Bearer valid"
    assert request.headers["accept"] == "application/json"
    assert request.url.params["name[ilike]"] == "%x%"


def test_raises_on_error_status():
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(fetch_dsm_api("/me/", "Bearer invalid"))


def test_get_me(client, dsm_requests):
    response = client.get("/me", headers={"authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json()["username"] == "jdoe"
    assert dsm_requests[-1].url.path == "/me/"


def test_get_me_without_authorization(client, dsm_requests):
    response = client.get("/me")

    assert response.status_code == 401
    assert dsm_requests == []


def test_get_me_rejected_by_dsm(client):
    response = client.get("/me", headers={"authorization": "Bearer invalid"})

    assert response.status_code == 502


def test_get_me_dsm_timeout(client, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout", request=request)

    monkeypatch.setattr(
        dsm_api,
        "_client",
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    response = client.get("/me", headers={"authorization": "Bearer valid"})

    assert response.status_code == 504


def test_fetch_own_database_usernames():
    usernames = asyncio.run(fetch_own_database_usernames("Bearer valid"))

    assert usernames == {
        "vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb",
        "vo_group3_0f1e2d3c4b5a69788796a5b4c3d2e1f0",
    }


def test_fetch_own_database_usernames_on_error_is_empty():
    assert asyncio.run(fetch_own_database_usernames("Bearer invalid")) == set()


def test_search_own_ingests():
    usernames = asyncio.run(search_own_ingests("Bearer valid", "x"))

    assert usernames == {"vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb"}


def test_endpoints_marks_own_and_adds_missing(client):
    response = client.get("/endpoints", headers={"authorization": "Bearer valid"})

    endpoints = response.json()["endpoints"]
    assert [e["name"] for e in endpoints if e["is_own"]] == [
        "vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb",
        "vo_group3_0f1e2d3c4b5a69788796a5b4c3d2e1f0",
    ]
