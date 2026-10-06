import httpx
import pytest
from fastapi.testclient import TestClient

import services.dsm_api as dsm_api
import services.frost_proxy as frost_proxy

FROST_ENDPOINTS = {
    "endpoints": [
        {
            "name": "vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb",
            "displayName": "vo group1",
            "group": "vo",
            "project": "group1",
            "url": "http://frost.:8080/sta/vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb/v1.1",
        },
        {
            "name": "vo_group2_86ebe19a704a496ca2c8053c2c6c3c17",
            "displayName": "vo group2",
            "group": "vo",
            "project": "group2",
            "url": "http://frost.:8080/sta/vo_group2_86ebe19a704a496ca2c8053c2c6c3c17/v1.1",
        },
    ]
}


@pytest.fixture
def frost_requests():
    """Collects the requests that reached the mocked FROST server."""
    return []


DSM_ME = {
    "id": 1,
    "username": "jdoe",
    "email": "jdoe@example.org",
    "given_name": "Jane",
    "family_name": "Doe",
    "is_active": True,
    "is_superuser": False,
}

DSM_PERMISSION_GROUPS = {
    "items": [
        {
            "id": 1,
            "name": "UFZ-TSM:Group One",
            "database_username": "vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb",
        },
        {
            "id": 2,
            "name": "UFZ-TSM:Sub:Group Three",
            "database_username": "vo_group3_0f1e2d3c4b5a69788796a5b4c3d2e1f0",
        },
    ]
}

DSM_INGESTS = [
    {
        "id": 10,
        "uuid": "6f1c0e3a-2b5d-4c8e-9a7f-1d2e3f4a5b6c",
        "name": "Weather Station",
        "permission_group_id": 1,
        "permission_group": {"id": 1, "name": "Group One"},
    },
    {
        "id": 11,
        "uuid": "0a9b8c7d-6e5f-4a3b-2c1d-0e9f8a7b6c5d",
        "name": "Soil Moisture 10",
        "permission_group_id": 2,
        "permission_group": {"id": 2, "name": "Group Three"},
    },
]


def filter_ingests(params: httpx.QueryParams) -> list[dict]:
    """Minimal emulation of the DSM API ingest filters (combined with AND)."""
    items = DSM_INGESTS
    if "id[eq]" in params:
        items = [i for i in items if str(i["id"]) == params["id[eq]"]]
    if "uuid[eq]" in params:
        items = [i for i in items if i["uuid"] == params["uuid[eq]"]]
    if "name[ilike]" in params:
        needle = params["name[ilike]"].strip("%").lower()
        items = [i for i in items if needle in i["name"].lower()]
    return items


@pytest.fixture
def dsm_requests():
    """Collects the requests that reached the mocked DSM API."""
    return []


@pytest.fixture(autouse=True)
def dsm_client(dsm_requests, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        dsm_requests.append(request)
        if request.headers.get("authorization") != "Bearer valid":
            return httpx.Response(401, json={"detail": "Not authenticated"})
        if request.url.path == "/me/":
            return httpx.Response(200, json=DSM_ME)
        if request.url.path == "/permission-group/":
            return httpx.Response(200, json=DSM_PERMISSION_GROUPS)
        if request.url.path == "/ingest/":
            return httpx.Response(
                200, json={"items": filter_ingests(request.url.params)}
            )
        return httpx.Response(404, json={"detail": "Not Found"})

    mock_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://dsm-api:8000",
    )
    monkeypatch.setattr(dsm_api, "_client", mock_client)
    return mock_client


@pytest.fixture
def client(frost_requests, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        frost_requests.append(request)
        if request.url.path == "/":
            return httpx.Response(200, json=FROST_ENDPOINTS)
        if "missing" in request.url.path:
            return httpx.Response(404, json={"message": "Nothing found."})
        return httpx.Response(200, json={"value": []})

    mock_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://frost:8080",
    )
    monkeypatch.setattr(frost_proxy, "_client", mock_client)

    from main import app

    return TestClient(app)
