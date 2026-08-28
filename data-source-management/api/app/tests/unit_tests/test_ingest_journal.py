"""Tests for the ingest/{id}/journal proxy router.

The router resolves the ingest (enforcing access via the repo) and proxies
to the timeio-db-api journal endpoint. httpx and the db-api settings are
mocked so no real db-api is needed.
"""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from config import settings
from dependencies import get_repo_ingest

ROUTER_MODULE = "routers.ingest_journal"
INGEST_UUID = "11111111-1111-1111-1111-111111111111"


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeAsyncClient:
    """Async-context-manager stand-in for httpx.AsyncClient."""

    last: "_FakeAsyncClient | None" = None

    def __init__(self, *args, **kwargs):
        self.payload = {"journal_entries": [{"id": 1, "level": "INFO"}]}
        self.calls = []
        _FakeAsyncClient.last = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, params=None, headers=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        return _FakeResponse(self.payload)


@pytest.fixture
def db_api_configured(monkeypatch):
    monkeypatch.setattr(settings, "DB_API_BASE_URL", "http://db-api:8001")
    monkeypatch.setattr(settings, "DB_API_AUTH_TOKEN", "test-token")


@pytest.fixture
def patch_httpx(monkeypatch):
    monkeypatch.setattr(f"{ROUTER_MODULE}.httpx.AsyncClient", _FakeAsyncClient)
    return _FakeAsyncClient


def test_get_journal_success(client, override_repo, db_api_configured, patch_httpx):
    repo = override_repo(get_repo_ingest)
    repo.find_one.return_value = SimpleNamespace(uuid=INGEST_UUID)

    response = client.get(f"/ingest/1/journal?level=INFO&limit=5")

    assert response.status_code == 200
    assert response.json() == {"journal_entries": [{"id": 1, "level": "INFO"}]}
    repo.find_one.assert_called_once()

    call = patch_httpx.last.calls[0]
    assert call["url"] == f"http://db-api:8001/things/{INGEST_UUID}/journal"
    assert call["params"] == {"limit": 5, "level": "INFO"}
    assert call["headers"]["Authorization"] == "Bearer test-token"


def test_get_journal_default_limit(
    client, override_repo, db_api_configured, patch_httpx
):
    repo = override_repo(get_repo_ingest)
    repo.find_one.return_value = SimpleNamespace(uuid=INGEST_UUID)

    response = client.get("/ingest/1/journal")

    assert response.status_code == 200
    assert patch_httpx.last.calls[0]["params"] == {"limit": 100}


def test_get_journal_not_found(client, override_repo, db_api_configured, patch_httpx):
    repo = override_repo(get_repo_ingest)
    repo.find_one.side_effect = HTTPException(status_code=404, detail="Not found")

    response = client.get("/ingest/999/journal")

    assert response.status_code == 404


def test_get_journal_db_api_not_configured(client, override_repo, monkeypatch):
    monkeypatch.setattr(settings, "DB_API_BASE_URL", "")
    repo = override_repo(get_repo_ingest)
    repo.find_one.return_value = SimpleNamespace(uuid=INGEST_UUID)

    response = client.get("/ingest/1/journal")

    assert response.status_code == 503
