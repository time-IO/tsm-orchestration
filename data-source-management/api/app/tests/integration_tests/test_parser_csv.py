"""
Integration tests for the parser/csv router.

Unlike the unit tests, these tests use a real database connection.
Each test creates data via the API, verifies it, and cleans up after
itself. This tests the full stack: router -> repository -> database.
"""

import json

import pytest
from sqlmodel import Session
from main import app
from dependencies import engine, get_current_user
from models import User
from ..utils.upload_files import make_csv_upload_file, as_multipart_file
from ..utils.user_proxy import UserProxy

BASE_PATH = "/parser/csv"


@pytest.fixture(autouse=True)
def _cleanup(cleanup_parser):
    yield


def _csv_payload(base_data, **overrides):
    payload = {
        "name": "Integration Test Csv Parser",
        "permission_group_id": base_data["permission_group_id"],
        "delimiter": ",",
        "timezone": "UTC",
        "encoding": "utf_8",
        "timestamp_columns": [{"column": 0, "timestamp_format": "%Y-%m-%d %H:%M:%S"}],
    }
    payload.update(overrides)
    return payload


def test_create_and_read(client, base_data):
    payload = _csv_payload(base_data)
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    created = response.json()
    assert created["name"] == "Integration Test Csv Parser"
    assert created["delimiter"] == ","
    assert len(created["timestamp_columns"]) == 1
    parser_id = created["id"]

    # read back
    response = client.get(f"{BASE_PATH}/{parser_id}")
    assert response.status_code == 200
    assert response.json()["id"] == parser_id


def test_create_and_update(client, base_data):
    payload = _csv_payload(base_data, name="Csv Parser To Update")
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    parser_id = response.json()["id"]

    response = client.patch(f"{BASE_PATH}/{parser_id}", json={"delimiter": ";"})
    assert response.status_code == 200
    assert response.json()["delimiter"] == ";"


def test_create_and_delete(client, base_data):
    payload = _csv_payload(base_data, name="Csv Parser To Delete")
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    parser_id = response.json()["id"]

    response = client.delete(f"{BASE_PATH}/{parser_id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    response = client.get(f"{BASE_PATH}/{parser_id}")
    assert response.status_code == 404


def test_read_list(client, base_data):
    for name in ["Csv Parser List A", "Csv Parser List B"]:
        client.post(f"{BASE_PATH}/", json=_csv_payload(base_data, name=name))

    response = client.get(f"{BASE_PATH}/")
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_read_not_found(client):
    response = client.get(f"{BASE_PATH}/99999")
    assert response.status_code == 404


def test_validate_parser(client, base_data):
    settings = _csv_payload(base_data)
    byte_size_slightly_less_than_one_megabyte = 1024 * 1024 - 100
    upload_file = make_csv_upload_file(byte_size_slightly_less_than_one_megabyte)
    response = client.post(
        f"{BASE_PATH}/parse",
        data={"settings": json.dumps(settings)},
        files={"file": as_multipart_file(upload_file, content_type="text/csv")},
    )
    assert response.status_code == 200
    assert response.json()["is_valid"] is True


def test_validate_parser_content_too_large(client, base_data):
    settings = _csv_payload(base_data)
    byte_size_slightly_more_than_one_megabyte = 1024 * 1024 + 100
    upload_file = make_csv_upload_file(byte_size_slightly_more_than_one_megabyte)
    response = client.post(
        f"{BASE_PATH}/parse",
        data={"settings": json.dumps(settings)},
        files={"file": as_multipart_file(upload_file, content_type="text/csv")},
    )
    assert response.status_code == 413


# --- auth / permission tests ---


def test_read_list_unauthenticated(client_no_auth):
    response = client_no_auth.get(f"{BASE_PATH}/")
    assert response.status_code == 401


def test_read_one_unauthenticated(client_no_auth):
    response = client_no_auth.get(f"{BASE_PATH}/1")
    assert response.status_code == 401


def test_create_unauthenticated(client_no_auth, base_data):
    response = client_no_auth.post(f"{BASE_PATH}/", json=_csv_payload(base_data))
    assert response.status_code == 401


def test_read_list_wrong_group_returns_empty(client, client_other_group, base_data):
    client.post(f"{BASE_PATH}/", json=_csv_payload(base_data))

    response = client_other_group.get(f"{BASE_PATH}/")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_read_one_wrong_group_returns_404(client, base_data, other_group_data):
    created_response = client.post(f"{BASE_PATH}/", json=_csv_payload(base_data))
    assert created_response.status_code == 200
    parser_id = created_response.json()["id"]

    with Session(engine) as s:
        other_user = s.get(User, other_group_data["user_id"])
        proxy = UserProxy(other_user, [other_group_data["permission_group_id"]])
    app.dependency_overrides[get_current_user] = lambda: proxy

    response = client.get(f"{BASE_PATH}/{parser_id}")
    assert response.status_code == 404
