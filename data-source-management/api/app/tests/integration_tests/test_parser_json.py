"""
Integration tests for the parser/json router.

Unlike the unit tests, these tests use a real database connection.
Each test creates data via the API, verifies it, and cleans up after
itself. This tests the full stack: router -> repository -> database.
"""

import io
import json
import warnings
from unittest.mock import patch

import pandas as pd
import pytest
from sqlmodel import Session
from starlette.datastructures import UploadFile
from timeio.errors import ParsingWarning
from main import app
from dependencies import engine, get_current_user
from models import User
from ..utils.user_proxy import UserProxy
from ..utils.upload_files import make_json_upload_file, as_multipart_file

BASE_PATH = "/parser/json"


def _upload_file(content: str, filename: str = "test.json") -> UploadFile:
    return UploadFile(file=io.BytesIO(content.encode("utf-8")), filename=filename)


@pytest.fixture(autouse=True)
def _cleanup(cleanup_parser):
    yield


def _json_payload(base_data, **overrides):
    payload = {
        "name": "Integration Test Json Parser",
        "permission_group_id": base_data["permission_group_id"],
        "timezone": "UTC",
        "timestamp_keys": [{"key": "timestamp", "format": "%Y-%m-%dT%H:%M:%S"}],
    }
    payload.update(overrides)
    return payload


def test_create_and_read(client, base_data):
    payload = _json_payload(base_data)
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    created = response.json()
    assert created["name"] == "Integration Test Json Parser"
    assert len(created["timestamp_keys"]) == 1
    assert created["timestamp_keys"][0]["key"] == "timestamp"
    parser_id = created["id"]

    # read back
    response = client.get(f"{BASE_PATH}/{parser_id}")
    assert response.status_code == 200
    assert response.json()["id"] == parser_id


def test_create_and_update(client, base_data):
    payload = _json_payload(base_data, name="Json Parser To Update")
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    parser_id = response.json()["id"]

    response = client.patch(f"{BASE_PATH}/{parser_id}", json={"comment": "updated"})
    assert response.status_code == 200
    assert response.json()["comment"] == "updated"


def test_create_and_delete(client, base_data):
    payload = _json_payload(base_data, name="Json Parser To Delete")
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    parser_id = response.json()["id"]

    response = client.delete(f"{BASE_PATH}/{parser_id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    response = client.get(f"{BASE_PATH}/{parser_id}")
    assert response.status_code == 404


def test_read_list(client, base_data):
    for name in ["Json Parser List A", "Json Parser List B"]:
        client.post(f"{BASE_PATH}/", json=_json_payload(base_data, name=name))

    response = client.get(f"{BASE_PATH}/")
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_read_not_found(client):
    response = client.get(f"{BASE_PATH}/99999")
    assert response.status_code == 404


def test_validate_content_size_valid(client, base_data):
    settings = _json_payload(base_data)
    byte_size_slightly_less_than_ten_megabyte = 1024 * 1024 * 10 - 100
    upload_file = make_json_upload_file(byte_size_slightly_less_than_ten_megabyte)
    response = client.post(
        f"{BASE_PATH}/validate",
        data={"settings": json.dumps(settings)},
        files={"file": as_multipart_file(upload_file, content_type="text/csv")},
    )
    assert response.status_code == 200
    assert response.json()["is_valid"] is True


def test_validate_content_too_large(client, base_data):
    settings = _json_payload(base_data)
    byte_size_slightly_more_than_ten_megabyte = 1024 * 1024 * 10 + 100
    upload_file = make_json_upload_file(byte_size_slightly_more_than_ten_megabyte)
    response = client.post(
        f"{BASE_PATH}/validate",
        data={"settings": json.dumps(settings)},
        files={"file": as_multipart_file(upload_file, content_type="text/csv")},
    )
    assert response.status_code == 413


def test_validate_passes_translated_settings_and_data_to_parser(client, base_data):
    settings = _json_payload(
        base_data,
        comment="note",
        timezone="Europe/Berlin",
        measurement_key="data",
        excluded_keys=["ignored"],
        timestamp_keys=[{"key": "ts", "format": "%Y-%m-%d"}],
    )
    file_content = '[{"ts": "2024-01-01", "data": 1}]'
    upload_file = _upload_file(f"\n{file_content}\n\n")

    with patch("services.parse_data.JsonParser") as MockJsonParser:
        MockJsonParser.return_value.do_parse.return_value = pd.DataFrame({"a": [1]})
        response = client.post(
            f"{BASE_PATH}/validate",
            data={"settings": json.dumps(settings)},
            files={"file": as_multipart_file(upload_file, content_type="text/csv")},
        )

    assert response.status_code == 200
    MockJsonParser.assert_called_once_with(
        {
            "comment": "note",
            "timestamp_keys": [{"key": "ts", "format": "%Y-%m-%d"}],
            "excluded_keys": ["ignored"],
            "measurement_key": "data",
            "timezone": "Europe/Berlin",
        }
    )
    do_parse = MockJsonParser.return_value.do_parse
    do_parse.assert_called_once_with(file_content, "project", "thing")


def test_validate_returns_parsed_data_from_parser_as_response(client, base_data):
    settings = _json_payload(base_data)
    upload_file = make_json_upload_file(50)
    fake_df = pd.DataFrame({"value": [10, 20]})

    with patch("services.parse_data.JsonParser") as MockJsonParser:
        MockJsonParser.return_value.do_parse.return_value = fake_df
        response = client.post(
            f"{BASE_PATH}/validate",
            data={"settings": json.dumps(settings)},
            files={"file": as_multipart_file(upload_file, content_type="text/csv")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is True
    assert body["error"] == ""
    assert body["warnings"] == []
    assert body["data"] == fake_df.reset_index().to_dict(orient="records")


def test_validate_returns_parser_exception_as_response(client, base_data):
    settings = _json_payload(base_data)
    upload_file = make_json_upload_file(50)

    with patch("services.parse_data.JsonParser") as MockJsonParser:
        MockJsonParser.return_value.do_parse.side_effect = ValueError(
            "something went wrong in the parser"
        )
        response = client.post(
            f"{BASE_PATH}/validate",
            data={"settings": json.dumps(settings)},
            files={"file": as_multipart_file(upload_file, content_type="text/csv")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is False
    assert body["error"] == "something went wrong in the parser"
    assert body["data"] == []


def test_validate_returns_parser_warnings_as_response(client, base_data):
    settings = _json_payload(base_data)
    upload_file = make_json_upload_file(50)
    fake_df = pd.DataFrame({"value": [1]})

    def fake_do_parse(*_args, **_kwargs):
        warnings.warn("something looked fishy", ParsingWarning)
        return fake_df

    with patch("services.parse_data.JsonParser") as MockJsonParser:
        MockJsonParser.return_value.do_parse.side_effect = fake_do_parse
        response = client.post(
            f"{BASE_PATH}/validate",
            data={"settings": json.dumps(settings)},
            files={"file": as_multipart_file(upload_file, content_type="text/csv")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is True
    assert body["warnings"] == ["something looked fishy"]


def test_read_list_unauthenticated(client_no_auth):
    response = client_no_auth.get(f"{BASE_PATH}/")
    assert response.status_code == 401


def test_read_one_unauthenticated(client_no_auth):
    response = client_no_auth.get(f"{BASE_PATH}/1")
    assert response.status_code == 401


def test_create_unauthenticated(client_no_auth, base_data):
    response = client_no_auth.post(f"{BASE_PATH}/", json=_json_payload(base_data))
    assert response.status_code == 401


def test_read_list_wrong_group_returns_empty(client, client_other_group, base_data):
    client.post(f"{BASE_PATH}/", json=_json_payload(base_data))

    response = client_other_group.get(f"{BASE_PATH}/")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_read_one_wrong_group_returns_404(client, base_data, other_group_data):
    created_response = client.post(f"{BASE_PATH}/", json=_json_payload(base_data))
    assert created_response.status_code == 200
    parser_id = created_response.json()["id"]

    with Session(engine) as s:
        other_user = s.get(User, other_group_data["user_id"])
        proxy = UserProxy(other_user, [other_group_data["permission_group_id"]])
    app.dependency_overrides[get_current_user] = lambda: proxy

    response = client.get(f"{BASE_PATH}/{parser_id}")
    assert response.status_code == 404
