"""Integration tests for the ingest/external-api/zentra router (real DB)."""

import pytest
from sqlmodel import Session
from main import app
from dependencies import engine, get_current_user
from ..utils.user_proxy import UserProxy
from models import User

BASE_PATH = "/ingest/external-api/zentra"


@pytest.fixture(autouse=True)
def _cleanup(cleanup_ingest):
    yield


def _zentra_payload(base_data, **overrides):
    payload = {
        "name": "Integration Test Zentra",
        "permission_group_id": base_data["permission_group_id"],
        "sync_enabled": True,
        "sync_interval_in_minutes": 15,
        "device_sn": "z6-00001",
        "period_in_minutes": 15,
        "api_key": "secret-key",
    }
    payload.update(overrides)
    return payload


def test_create_and_read(client, base_data):
    response = client.post(f"{BASE_PATH}", json=_zentra_payload(base_data))
    assert response.status_code == 200
    created = response.json()
    assert created["name"] == "Integration Test Zentra"
    assert created["device_sn"] == "z6-00001"
    assert created["api_type"] == "zentra"
    assert created["period_in_minutes"] == 15
    assert created["units"] == "metric"
    assert created["api_key"] == "secret-key"
    ingest_id = created["id"]

    response = client.get(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 200
    assert response.json()["id"] == ingest_id
    assert response.json()["units"] == "metric"


def test_create_and_update(client, base_data):
    payload = _zentra_payload(base_data, name="Zentra To Update")
    response = client.post(f"{BASE_PATH}", json=payload)
    assert response.status_code == 200
    ingest_id = response.json()["id"]

    response = client.patch(f"{BASE_PATH}/{ingest_id}", json={"device_sn": "z6-00002"})
    assert response.status_code == 200
    assert response.json()["device_sn"] == "z6-00002"

    response = client.patch(f"{BASE_PATH}/{ingest_id}", json={"period_in_minutes": 30})
    assert response.status_code == 200
    assert response.json()["period_in_minutes"] == 30

    response = client.patch(f"{BASE_PATH}/{ingest_id}", json={"units": "imperial"})
    assert response.status_code == 200
    assert response.json()["units"] == "imperial"

    response = client.patch(f"{BASE_PATH}/{ingest_id}", json={"api_key": "new-key"})
    assert response.status_code == 200
    assert response.json()["api_key"] == "new-key"


def test_create_and_delete(client, base_data):
    payload = _zentra_payload(base_data, name="Zentra To Delete")
    response = client.post(f"{BASE_PATH}", json=payload)
    assert response.status_code == 200
    ingest_id = response.json()["id"]

    response = client.delete(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    response = client.get(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 404


def test_read_list(client, base_data):
    for name in ["Zentra List A", "Zentra List B"]:
        client.post(f"{BASE_PATH}/", json=_zentra_payload(base_data, name=name))

    response = client.get(f"{BASE_PATH}/")
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_read_not_found(client):
    response = client.get(f"{BASE_PATH}/99999")
    assert response.status_code == 404


# --- auth / permission tests ---
def test_read_list_unauthenticated(client_no_auth):
    response = client_no_auth.get(f"{BASE_PATH}/")
    assert response.status_code == 401


def test_read_one_unauthenticated(client_no_auth):
    response = client_no_auth.get(f"{BASE_PATH}/1")
    assert response.status_code == 401


def test_create_unauthenticated(client_no_auth, base_data):
    response = client_no_auth.post(f"{BASE_PATH}/", json=_zentra_payload(base_data))
    assert response.status_code == 401


def test_read_list_wrong_group_returns_empty(client, client_other_group, base_data):
    client.post(f"{BASE_PATH}/", json=_zentra_payload(base_data))

    response = client_other_group.get(f"{BASE_PATH}/")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_read_one_wrong_group_returns_404(client, base_data, other_group_data):
    created_response = client.post(f"{BASE_PATH}/", json=_zentra_payload(base_data))
    assert created_response.status_code == 200
    ingest_id = created_response.json()["id"]

    with Session(engine) as s:
        other_user = s.get(User, other_group_data["user_id"])
        proxy = UserProxy(other_user, [other_group_data["permission_group_id"]])
    app.dependency_overrides[get_current_user] = lambda: proxy

    response = client.get(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 404
