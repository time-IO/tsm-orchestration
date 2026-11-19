"""Tests for the ingest/external-api/zentra router (full CRUD, mocked repo)."""

import pytest
from fastapi import HTTPException

from dependencies import get_repo_ingest_external_api_zentra

ROUTER_MODULE = "routers.ingest_external_api_zentra"
BASE_PATH = "/ingest/external-api/zentra"


def _zentra_dict(make_ingest_dict, **overrides):
    defaults = {
        "api_type": "zentra",
        "sync_enabled": True,
        "sync_interval_in_minutes": None,
        "device_sn": "z6-00001",
        "period_in_minutes": 15,
        "units": "metric",
        "api_key": "secret-key",
    }
    defaults.update(overrides)
    return make_ingest_dict(**defaults)


# ---------------------------------------------------------------------------
# read_one
# ---------------------------------------------------------------------------


def test_read_one_found(client, override_repo, make_ingest_dict):
    repo = override_repo(get_repo_ingest_external_api_zentra)
    repo.find_one.return_value = object()
    repo.to_flat.return_value = _zentra_dict(make_ingest_dict)

    response = client.get(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json()["device_sn"] == "z6-00001"
    repo.find_one.assert_called_once()


def test_read_one_not_found(client, override_repo):
    repo = override_repo(get_repo_ingest_external_api_zentra)
    repo.find_one.side_effect = HTTPException(status_code=404, detail="Not found")

    response = client.get(f"{BASE_PATH}/999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_external_api_zentra)
    repo.create.return_value = object()
    repo.to_flat.return_value = _zentra_dict(make_ingest_dict)
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    payload = {
        "name": "Test Zentra",
        "permission_group_id": 1,
        "sync_enabled": True,
        "sync_interval_in_minutes": 15,
        "device_sn": "z6-00001",
        "period_in_minutes": 15,
        "units": "metric",
        "api_key": "secret-key",
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 200
    repo.create.assert_called_once()
    mock_publish.assert_called_once()


def test_create_missing_api_key(client, override_repo):
    override_repo(get_repo_ingest_external_api_zentra)
    payload = {
        "name": "Test Zentra",
        "permission_group_id": 1,
        "device_sn": "z6-00001",
        "period_in_minutes": 15,
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 422


def test_create_invalid_units(client, override_repo):
    override_repo(get_repo_ingest_external_api_zentra)
    payload = {
        "name": "Test Zentra",
        "permission_group_id": 1,
        "device_sn": "z6-00001",
        "period_in_minutes": 15,
        "units": "kelvin",
        "api_key": "secret-key",
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_external_api_zentra)
    repo.update.return_value = object()
    repo.to_flat.return_value = _zentra_dict(make_ingest_dict, units="imperial")
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    response = client.patch(f"{BASE_PATH}/1", json={"units": "imperial"})

    assert response.status_code == 200
    assert response.json()["units"] == "imperial"
    repo.update.assert_called_once()
    mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete(client, override_repo):
    repo = override_repo(get_repo_ingest_external_api_zentra)
    repo.delete.return_value = {"ok": True}

    response = client.delete(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    repo.delete.assert_called_once()
