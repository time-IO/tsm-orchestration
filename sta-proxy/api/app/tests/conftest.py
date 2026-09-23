import httpx
import pytest
from fastapi.testclient import TestClient

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
