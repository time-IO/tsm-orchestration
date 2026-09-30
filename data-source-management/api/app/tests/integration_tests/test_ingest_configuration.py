"""
Integration tests for GET /ingest/{id}/configurations.

The ingest is resolved from the real database (including the access
check); only the external timeio-db-api is replaced by FakeDbApi.
"""

import pytest

from config import settings
from ..utils.db_api import thing_path

SMS_ROOT_URL = "https://sms.example.com/"
DB_API_CONFIGURATIONS = [
    {"id": 7, "label": "Station A"},
    {"id": 42, "label": "Station B"},
]


@pytest.fixture(autouse=True)
def _sms_root_url(monkeypatch):
    monkeypatch.setattr(settings, "SMS_ROOT_URL", SMS_ROOT_URL)


def test_links_configurations_to_sms(client, mqtt_ingest, db_api):
    db_api.stub_thing(mqtt_ingest["uuid"], "configurations", json=DB_API_CONFIGURATIONS)

    response = client.get(f"/ingest/{mqtt_ingest['id']}/configurations")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 7,
            "label": "Station A",
            "url": "https://sms.example.com/configurations/7",
        },
        {
            "id": 42,
            "label": "Station B",
            "url": "https://sms.example.com/configurations/42",
        },
    ]

    request = db_api.last_request
    assert request.path == thing_path(mqtt_ingest["uuid"], "configurations")
    assert request.authorization == db_api.expected_authorization


def test_no_configurations(client, mqtt_ingest, db_api):
    db_api.stub_thing(mqtt_ingest["uuid"], "configurations", json=[])

    response = client.get(f"/ingest/{mqtt_ingest['id']}/configurations")

    assert response.status_code == 200
    assert response.json() == []


def test_unknown_ingest_returns_404(client, db_api):
    response = client.get("/ingest/999999999/configurations")

    assert response.status_code == 404
    assert db_api.requests == []


def test_ingest_of_other_group_returns_404(
    client, mqtt_ingest, switch_to_other_group, db_api
):
    switch_to_other_group()

    response = client.get(f"/ingest/{mqtt_ingest['id']}/configurations")

    assert response.status_code == 404
    assert db_api.requests == []


def test_db_api_error_returns_502(client, mqtt_ingest, db_api):
    db_api.stub_thing(mqtt_ingest["uuid"], "configurations", status_code=500)

    response = client.get(f"/ingest/{mqtt_ingest['id']}/configurations")

    assert response.status_code == 502


def test_db_api_not_configured_returns_503(client, mqtt_ingest, db_api_unconfigured):
    response = client.get(f"/ingest/{mqtt_ingest['id']}/configurations")

    assert response.status_code == 503
