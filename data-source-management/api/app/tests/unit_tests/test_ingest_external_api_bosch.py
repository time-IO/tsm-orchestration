"""
Tests for the ingest/external-api/bosch router (full CRUD).

Differences from the plain list router:
- read_one: repo.find_one(...) is passed to repo.to_flat(...).
  Since the repo is fully mocked, find_one's return value content
  is irrelevant - only to_flat.return_value matters for the response.
- create/update: trigger publish_frontend_thing_update(entity) (a real
  MQTT call) -> suppressed via mock_publish_frontend_update (monkeypatch).
- create/update: also depend on create_database_if_not_exists, which
  is already neutralized globally in the client fixture.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from access_scope import AccessScope
from dependencies import get_repo_ingest_external_api_bosch
from repositories.ingest_external_api_bosch import IngestExternalApiBoschRepository

ROUTER_MODULE = "routers.ingest_external_api_bosch"
BASE_PATH = "/ingest/external-api/bosch"


def _bosch_dict(make_ingest_dict, **overrides):
    """Builds a dict for IngestExternalApiBoschRead: IngestRead fields
    (via make_ingest_dict) + IngestExternalApiRead fields (api_type,
    sync_enabled, sync_interval_in_minutes) + Bosch-specific fields.
    Merge first, then call - otherwise an override collides with a
    same-named default keyword arg (e.g. sensor_id)."""
    defaults = {
        "api_type": "bosch",
        "sync_enabled": True,
        "sync_interval_in_minutes": None,
        "endpoint": "https://example.com",
        "sensor_id": "sensor-1",
        "bosch_username": "user",
        "bosch_password": "secret",
        "period_in_minutes": 10,
    }
    defaults.update(overrides)
    return make_ingest_dict(**defaults)


# ---------------------------------------------------------------------------
# read_list
# ---------------------------------------------------------------------------


def test_read_list_passes_superuser_access_scope(client, mock_user, override_repo):
    mock_user.is_superuser = True
    repo = override_repo(get_repo_ingest_external_api_bosch)
    repo.find_all.return_value = []

    response = client.get(f"{BASE_PATH}/")

    assert response.status_code == 200
    access_scope = repo.find_all.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_find_all_does_not_filter_superuser_by_permission_group():
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalars.return_value.all.return_value = (
        []
    )
    repo = IngestExternalApiBoschRepository(session)

    repo.find_all(access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert statement.whereclause is None


# ---------------------------------------------------------------------------
# read_one
# ---------------------------------------------------------------------------


def test_read_one_found(client, override_repo, make_ingest_dict):
    repo = override_repo(get_repo_ingest_external_api_bosch)
    repo.find_one.return_value = object()  # content irrelevant, to_flat is mocked
    repo.to_flat.return_value = _bosch_dict(make_ingest_dict)

    response = client.get(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json()["sensor_id"] == "sensor-1"
    repo.find_one.assert_called_once()


def test_read_one_not_found(client, override_repo):
    repo = override_repo(get_repo_ingest_external_api_bosch)
    repo.find_one.side_effect = HTTPException(status_code=404, detail="Not found")

    response = client.get(f"{BASE_PATH}/999")

    assert response.status_code == 404


def test_read_one_passes_superuser_access_scope(
    client, mock_user, override_repo, make_ingest_dict
):
    mock_user.is_superuser = True
    repo = override_repo(get_repo_ingest_external_api_bosch)
    repo.find_one.return_value = object()
    repo.to_flat.return_value = _bosch_dict(make_ingest_dict)

    response = client.get(f"{BASE_PATH}/1")

    assert response.status_code == 200
    access_scope = repo.find_one.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_external_api_bosch)
    repo.create.return_value = (
        object()
    )  # passed to publish_frontend_thing_update + to_flat, content irrelevant
    repo.to_flat.return_value = _bosch_dict(make_ingest_dict)
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    payload = {
        "name": "Test Bosch",
        "permission_group_id": 1,
        "sync_enabled": True,
        "sync_interval_in_minutes": 15,
        "endpoint": "https://example.com",
        "sensor_id": "sensor-1",
        "bosch_username": "user",
        "bosch_password": "secret",
        "period_in_minutes": 10,
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 200
    repo.create.assert_called_once()
    mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_external_api_bosch)
    repo.update.return_value = object()
    repo.to_flat.return_value = _bosch_dict(make_ingest_dict, sensor_id="sensor-2")
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    # Update schema: all fields optional (PATCH semantics) -> a single
    # field is enough, the rest stays unchanged
    payload = {"sensor_id": "sensor-2"}

    response = client.patch(f"{BASE_PATH}/1", json=payload)

    assert response.status_code == 200
    assert response.json()["sensor_id"] == "sensor-2"
    repo.update.assert_called_once()
    mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete(client, override_repo):
    repo = override_repo(get_repo_ingest_external_api_bosch)
    repo.delete.return_value = {"ok": True}

    response = client.delete(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    repo.delete.assert_called_once()
