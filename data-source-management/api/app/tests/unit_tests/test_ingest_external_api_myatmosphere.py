"""Tests for the ingest/external-api/myatmosphere router (full CRUD, mocked repo)."""

import pytest
from fastapi import HTTPException

from dependencies import get_repo_ingest_external_api_myatmosphere

ROUTER_MODULE = "routers.ingest_external_api_myatmosphere"
BASE_PATH = "/ingest/external-api/myatmosphere"


def _myatmosphere_dict(make_ingest_dict, **overrides):
    defaults = {
        "api_type": "myatmosphere",
        "sync_enabled": True,
        "sync_interval_in_minutes": None,
        "customer_id": 479,
        "serial_number": "22935",
        "period_in_minutes": 15,
        "api_key": "secret-key",
    }
    defaults.update(overrides)
    return make_ingest_dict(**defaults)


# ---------------------------------------------------------------------------
# read_one
# ---------------------------------------------------------------------------


def test_read_one_found(client, override_repo, make_ingest_dict):
    repo = override_repo(get_repo_ingest_external_api_myatmosphere)
    repo.find_one.return_value = object()
    repo.to_flat.return_value = _myatmosphere_dict(make_ingest_dict)

    response = client.get(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json()["serial_number"] == "22935"
    repo.find_one.assert_called_once()


def test_read_one_not_found(client, override_repo):
    repo = override_repo(get_repo_ingest_external_api_myatmosphere)
    repo.find_one.side_effect = HTTPException(status_code=404, detail="Not found")

    response = client.get(f"{BASE_PATH}/999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_external_api_myatmosphere)
    repo.create.return_value = object()
    repo.to_flat.return_value = _myatmosphere_dict(make_ingest_dict)
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    payload = {
        "name": "Test MyAtmosphere",
        "permission_group_id": 1,
        "sync_enabled": True,
        "sync_interval_in_minutes": 15,
        "customer_id": 479,
        "serial_number": "22935",
        "period_in_minutes": 15,
        "api_key": "secret-key",
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 200
    repo.create.assert_called_once()
    mock_publish.assert_called_once()


def test_create_missing_api_key(client, override_repo):
    override_repo(get_repo_ingest_external_api_myatmosphere)
    payload = {
        "name": "Test MyAtmosphere",
        "permission_group_id": 1,
        "customer_id": 479,
        "serial_number": "22935",
        "period_in_minutes": 15,
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field, value",
    [
        ("customer_id", 0),
        ("serial_number", ""),
        ("period_in_minutes", 0),
        ("api_key", ""),
    ],
)
def test_create_invalid_field(client, override_repo, field, value):
    override_repo(get_repo_ingest_external_api_myatmosphere)
    payload = {
        "name": "Test MyAtmosphere",
        "permission_group_id": 1,
        "customer_id": 479,
        "serial_number": "22935",
        "period_in_minutes": 15,
        "api_key": "secret-key",
        field: value,
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_external_api_myatmosphere)
    repo.update.return_value = object()
    repo.to_flat.return_value = _myatmosphere_dict(
        make_ingest_dict, serial_number="22938"
    )
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    response = client.patch(f"{BASE_PATH}/1", json={"serial_number": "22938"})

    assert response.status_code == 200
    assert response.json()["serial_number"] == "22938"
    repo.update.assert_called_once()
    mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete(client, override_repo):
    repo = override_repo(get_repo_ingest_external_api_myatmosphere)
    repo.delete.return_value = {"ok": True}

    response = client.delete(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    repo.delete.assert_called_once()
