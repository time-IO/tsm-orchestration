from types import SimpleNamespace

import httpx
import pytest

from config import settings
from dependencies import get_repo_database

BASE_PATH = "/sta/"
TOKEN = "test-token"
DATABASE_USERNAME = "ufztsm_project_abc"


@pytest.fixture
def mock_user():
    """Member of the permission group 1."""
    return SimpleNamespace(id=1, permission_group_ids=[1], is_superuser=False)


def mock_sta_transport(monkeypatch, handler):
    """Send the proxy's outgoing STA requests to ``handler`` instead of the network."""
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        "services.sta_proxy.AsyncClient",
        lambda *args, **kwargs: real_client(transport=httpx.MockTransport(handler)),
    )


@pytest.fixture(autouse=True)
def database_repo(override_repo, monkeypatch):
    monkeypatch.setattr(settings, "STA_ROOT_URL", "http://proxy/sta/")
    monkeypatch.setattr(settings, "STA_VERSION", "/v1.1/")
    repo = override_repo(get_repo_database)
    repo.find_one_permission_group_id.return_value = SimpleNamespace(
        username=DATABASE_USERNAME
    )
    return repo


def get_sta(client, query: str):
    return client.get(
        BASE_PATH,
        params={"permission_group_id": 1, "q": query},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )


def test_queries_internal_endpoint(client, monkeypatch):
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"value": []})

    mock_sta_transport(monkeypatch, handler)

    response = get_sta(client, "Datastreams?$top=10")

    assert response.status_code == 200
    assert len(requests) == 1
    assert requests[0].url.path == f"/sta/internal/{DATABASE_USERNAME}/v1.1/Datastreams"
    assert requests[0].headers["Authorization"] == f"Bearer {TOKEN}"


@pytest.mark.parametrize("status_code", [401, 403, 404])
def test_passes_sta_errors_through(client, monkeypatch, status_code):
    mock_sta_transport(
        monkeypatch, lambda request: httpx.Response(status_code, json={"detail": "x"})
    )

    assert get_sta(client, "Datastreams").status_code == status_code


def test_sta_not_reachable_returns_502(client, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    mock_sta_transport(monkeypatch, handler)

    assert get_sta(client, "Datastreams").status_code == 502
