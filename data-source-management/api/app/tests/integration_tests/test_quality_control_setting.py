"""
Integration tests for the quality-control-setting router.

Unlike the unit tests, these tests use a real database connection.
Each test creates data via the API, verifies it, and cleans up after
itself. This tests the full stack: router -> repository -> database.
"""

import pytest
from sqlmodel import Session
from main import app
from dependencies import engine, get_current_user
from ..utils.user_proxy import UserProxy
from models import User

BASE_PATH = "/quality-control-setting"


@pytest.fixture(autouse=True)
def _cleanup(cleanup_qc):
    yield


def _dummy_datastream():
    return {
        "@iot.id": 1,
        "alias": "dummy",
        "Thing": {"@iot.id": 1},
    }


def _qc_payload(base_data, **overrides):
    payload = {
        "name": "Integration Test QC Setting",
        "permission_group_id": base_data["permission_group_id"],
        "context_window": "1D",
        "is_active": False,
        "quality_control_functions": [
            {
                "name": "propagateFlags",
                "quality_control_function_arguments": [
                    {
                        "name": "field",
                        "type": "datastream",
                        "input": {"value": [_dummy_datastream()]},
                    },
                    {
                        "name": "target",
                        "type": "datastream",
                        "input": {"value": [_dummy_datastream()]},
                    },
                    {
                        "name": "flag",
                        "type": "float",
                        "input": {"value": 255.0},
                    },
                ],
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_create_and_read(client, base_data):
    payload = _qc_payload(base_data)
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    created = response.json()
    assert created["name"] == "Integration Test QC Setting"
    assert len(created["quality_control_functions"]) == 1
    assert created["quality_control_functions"][0]["name"] == "propagateFlags"
    qc_id = created["id"]

    # read back
    response = client.get(f"{BASE_PATH}/{qc_id}")
    assert response.status_code == 200
    assert response.json()["id"] == qc_id


def test_create_and_update(client, base_data):
    payload = _qc_payload(base_data, name="QC Setting To Update")
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    qc_id = response.json()["id"]

    response = client.patch(f"{BASE_PATH}/{qc_id}", json={"is_active": True})
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_create_and_delete(client, base_data):
    payload = _qc_payload(base_data, name="QC Setting To Delete")
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    qc_id = response.json()["id"]

    response = client.delete(f"{BASE_PATH}/{qc_id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    response = client.get(f"{BASE_PATH}/{qc_id}")
    assert response.status_code == 404


def test_read_list(client, base_data):
    for name in ["QC Setting List A", "QC Setting List B"]:
        client.post(f"{BASE_PATH}/", json=_qc_payload(base_data, name=name))

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
    response = client_no_auth.post(f"{BASE_PATH}/", json=_qc_payload(base_data))
    assert response.status_code == 401


def test_read_list_wrong_group_returns_empty(client, client_other_group, base_data):
    client.post(f"{BASE_PATH}/", json=_qc_payload(base_data))

    response = client_other_group.get(f"{BASE_PATH}/")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_read_one_wrong_group_returns_404(client, base_data, other_group_data):
    created_response = client.post(f"{BASE_PATH}/", json=_qc_payload(base_data))
    assert created_response.status_code == 200
    qc_id = created_response.json()["id"]

    with Session(engine) as s:
        other_user = s.get(User, other_group_data["user_id"])
        proxy = UserProxy(other_user, [other_group_data["permission_group_id"]])
    app.dependency_overrides[get_current_user] = lambda: proxy

    response = client.get(f"{BASE_PATH}/{qc_id}")
    assert response.status_code == 404
