"""
Tests for the ingest/mqtt router (full CRUD).

Differences from the other unit_tests:
- All mqtt-specific fields (topic, uri, username, password,
  password_hashed) are generated server-side in create() - the
  Create schema only accepts parser_id (plus the inherited base
  Ingest fields like name, permission_group_id).
- update() uses the generic IngestUpdate schema (not a mqtt-specific
  one) - only base Ingest fields (name, description,
  permission_group_id, parser_id) can be changed, no mqtt-specific
  fields.
- No parser_repo permission check here (unlike the sftp unit_tests) -
  create() doesn't validate parser_id against permission groups.
- to_flat() builds a nested "parser" dict in addition to the nested
  "permission_group" dict - needs a dummy value in make_ingest_dict
  overrides.
- parser_id is a required (non-Optional) int in IngestMqttRead, so
  it must always be overridden away from make_ingest_dict's None
  default.
"""

import pytest
from fastapi import HTTPException

from dependencies import get_repo_ingest_mqtt

ROUTER_MODULE = "routers.ingest_mqtt"
BASE_PATH = "/ingest/mqtt"


def _mqtt_dict(make_ingest_dict, **overrides):
    """Builds a dict for IngestMqttRead: IngestRead fields (via
    make_ingest_dict) + mqtt-specific fields."""
    defaults = {
        "parser_id": 1,
        "topic": "mqtt_ingest/ingest-mqtt-test",
        "uri": "mqtt://broker.example.com:1883",
        "username": "ingest-mqtt-test",
        "password": "secret",
        "password_hashed": "hashed-secret",
        "parser": {"id": 1, "name": "Default Parser"},
    }
    defaults.update(overrides)
    return make_ingest_dict(**defaults)


# ---------------------------------------------------------------------------
# read_one
# ---------------------------------------------------------------------------


def test_read_one_found(client, override_repo, make_ingest_dict):
    repo = override_repo(get_repo_ingest_mqtt)
    repo.find_one.return_value = object()  # content irrelevant, to_flat is mocked
    repo.to_flat.return_value = _mqtt_dict(make_ingest_dict)

    response = client.get(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json()["topic"] == "mqtt_ingest/ingest-mqtt-test"
    repo.find_one.assert_called_once()


def test_read_one_not_found(client, override_repo):
    repo = override_repo(get_repo_ingest_mqtt)
    repo.find_one.side_effect = HTTPException(status_code=404, detail="Not found")

    response = client.get(f"{BASE_PATH}/999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_mqtt)
    repo.create.return_value = (
        object()
    )  # passed to publish_frontend_thing_update + to_flat, content irrelevant
    repo.to_flat.return_value = _mqtt_dict(make_ingest_dict)
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    payload = {
        "name": "Test MQTT",
        "permission_group_id": 1,
        "parser_id": 1,
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 200
    repo.create.assert_called_once()
    mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_mqtt)
    repo.update.return_value = object()
    repo.to_flat.return_value = _mqtt_dict(make_ingest_dict, name="Renamed MQTT")
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    # Update uses the generic IngestUpdate schema - only base Ingest
    # fields are changeable, e.g. name
    payload = {"name": "Renamed MQTT"}

    response = client.patch(f"{BASE_PATH}/1", json=payload)

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed MQTT"
    repo.update.assert_called_once()
    mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete(client, override_repo):
    repo = override_repo(get_repo_ingest_mqtt)
    repo.delete.return_value = {"ok": True}

    response = client.delete(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    repo.delete.assert_called_once()
