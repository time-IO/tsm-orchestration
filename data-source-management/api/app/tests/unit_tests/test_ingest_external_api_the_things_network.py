"""
Tests for the ingest/external-api/the_things_network router (full CRUD).

Differences from the plain list router:
- read_one: repo.find_one(...) is passed to repo.to_flat(...).
  Since the repo is fully mocked, find_one's return value content
  is irrelevant - only to_flat.return_value matters for the response.
- create/update: trigger publish_frontend_thing_update(entity) (a real
  MQTT call) -> suppressed via mock_publish_frontend_update (monkeypatch).
- create/update: also depend on create_database_if_not_exists, which
  is already neutralized globally in the client fixture.
"""

import pytest
from fastapi import HTTPException

from dependencies import get_repo_ingest_external_api_the_things_network

ROUTER_MODULE = "routers.ingest_external_api_the_things_network"
BASE_PATH = "/ingest/external-api/the-things-network"


def _the_things_network_dict(make_ingest_dict, **overrides):
    """Builds a dict for IngestExternalApithe_things_networkRead: IngestRead fields
    (via make_ingest_dict) + IngestExternalApiRead fields (api_type,
    sync_enabled, sync_interval_in_minutes) + the_things_network-specific fields.
    Merge first, then call - otherwise an override collides with a
    same-named default keyword arg (e.g. sensor_id)."""
    defaults = {
        "api_type": "the_things_network",
        "sync_enabled": True,
        "sync_interval_in_minutes": None,
        "api_key": "Exampel-Key",
        "endpoint_uri": "Example-URI",
    }
    defaults.update(overrides)
    return make_ingest_dict(**defaults)


# ---------------------------------------------------------------------------
# read_one
# ---------------------------------------------------------------------------


def test_read_one_found(client, override_repo, make_ingest_dict):
    repo = override_repo(get_repo_ingest_external_api_the_things_network)
    repo.find_one.return_value = object()  # content irrelevant, to_flat is mocked
    repo.to_flat.return_value = _the_things_network_dict(make_ingest_dict)

    response = client.get(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json()["api_key"] == "Exampel-Key"
    repo.find_one.assert_called_once()


def test_read_one_not_found(client, override_repo):
    repo = override_repo(get_repo_ingest_external_api_the_things_network)
    repo.find_one.side_effect = HTTPException(status_code=404, detail="Not found")

    response = client.get(f"{BASE_PATH}/999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_external_api_the_things_network)
    repo.create.return_value = (
        object()
    )  # passed to publish_frontend_thing_update + to_flat, content irrelevant
    repo.to_flat.return_value = _the_things_network_dict(make_ingest_dict)
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    payload = {
        "name": "Test the_things_network",
        "permission_group_id": 1,
        "sync_enabled": True,
        "api_key": "Exampel-Key",
        "endpoint_uri": "Example-URI",
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 200
    repo.create.assert_called_once()
    mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_external_api_the_things_network)
    repo.update.return_value = object()
    repo.to_flat.return_value = _the_things_network_dict(
        make_ingest_dict, api_key="Exampel-Key2"
    )
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    # Update schema: all fields optional (PATCH semantics) -> a single
    # field is enough, the rest stays unchanged
    payload = {"api_key": "Exampel-Key2"}

    response = client.patch(f"{BASE_PATH}/1", json=payload)

    assert response.status_code == 200
    assert response.json()["api_key"] == "Exampel-Key2"
    repo.update.assert_called_once()
    mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete(client, override_repo):
    repo = override_repo(get_repo_ingest_external_api_the_things_network)
    repo.delete.return_value = {"ok": True}

    response = client.delete(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    repo.delete.assert_called_once()
