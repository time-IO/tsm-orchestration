"""
Integration tests for the ingest/external-api/sensoto router.

Unlike the unit tests, these tests use a real database connection.
Each test creates data via the API, verifies it, and cleans up after
itself. This tests the full stack: router -> repository -> database.
"""

import pytest
from sqlmodel import Session, text
from main import app
from dependencies import engine, get_current_user
from tests.utils.user_proxy import UserProxy
from models import User

BASE_PATH = "/ingest/external-api/sensoto"


@pytest.fixture(autouse=True)
def _cleanup(cleanup_ingest):
    yield


def _sensoto_payload(base_data, **overrides):
    payload = {
        "name": "Integration Test Sensoto",
        "permission_group_id": base_data["permission_group_id"],
        "sync_enabled": True,
        "sync_interval_in_minutes": 15,
        "network": "network-1",
        "device": "device-1",
    }
    payload.update(overrides)
    return payload


def test_create_and_read(client, base_data):
    payload = _sensoto_payload(base_data)
    response = client.post(f"{BASE_PATH}", json=payload)
    assert response.status_code == 200
    created = response.json()
    assert created["name"] == "Integration Test Sensoto"
    assert created["network"] == "network-1"
    assert created["device"] == "device-1"
    assert created["api_type"] == "sensoto"
    ingest_id = created["id"]

    # read back
    response = client.get(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 200
    assert response.json()["id"] == ingest_id


def test_create_and_update(client, base_data):
    payload = _sensoto_payload(base_data, name="Sensoto To Update")
    response = client.post(f"{BASE_PATH}", json=payload)
    assert response.status_code == 200
    ingest_id = response.json()["id"]

    response = client.patch(f"{BASE_PATH}/{ingest_id}", json={"device": "device-2"})
    assert response.status_code == 200
    assert response.json()["device"] == "device-2"


def test_create_and_delete(client, base_data):
    payload = _sensoto_payload(base_data, name="Sensoto To Delete")
    response = client.post(f"{BASE_PATH}", json=payload)
    assert response.status_code == 200
    ingest_id = response.json()["id"]

    response = client.delete(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    response = client.get(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 404


def test_read_list(client, base_data):
    for name in ["Sensoto List A", "Sensoto List B"]:
        client.post(f"{BASE_PATH}/", json=_sensoto_payload(base_data, name=name))

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
    response = client_no_auth.post(f"{BASE_PATH}/", json=_sensoto_payload(base_data))
    assert response.status_code == 401


def test_read_list_wrong_group_returns_empty(client, client_other_group, base_data):
    client.post(f"{BASE_PATH}/", json=_sensoto_payload(base_data))

    response = client_other_group.get(f"{BASE_PATH}/")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_read_one_wrong_group_returns_404(client, base_data, other_group_data):
    created_response = client.post(f"{BASE_PATH}/", json=_sensoto_payload(base_data))
    assert created_response.status_code == 200
    ingest_id = created_response.json()["id"]

    with Session(engine) as s:
        other_user = s.get(User, other_group_data["user_id"])
        proxy = UserProxy(other_user, [other_group_data["permission_group_id"]])
    app.dependency_overrides[get_current_user] = lambda: proxy

    response = client.get(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 404
