from ..utils.db_api_mock import thing_path

JOURNAL = {"journal_entries": [{"id": 1, "level": "INFO"}]}


def test_proxies_journal_from_db_api(client, mqtt_ingest, db_api):
    db_api.stub_thing(mqtt_ingest["uuid"], "journal", json=JOURNAL)

    response = client.get(
        f"/ingest/{mqtt_ingest['id']}/journal", params={"level": "INFO", "limit": 5}
    )

    assert response.status_code == 200
    assert response.json() == JOURNAL

    request = db_api.last_request
    assert request.path == thing_path(mqtt_ingest["uuid"], "journal")
    assert request.params == {"limit": "5", "level": "INFO"}
    assert request.authorization == db_api.expected_authorization


def test_uses_default_limit(client, mqtt_ingest, db_api):
    db_api.stub_thing(mqtt_ingest["uuid"], "journal", json=JOURNAL)

    response = client.get(f"/ingest/{mqtt_ingest['id']}/journal")

    assert response.status_code == 200
    assert db_api.last_request.params == {"limit": "100"}


def test_unknown_ingest_returns_404(client, db_api):
    response = client.get("/ingest/999999999/journal")

    assert response.status_code == 404
    assert db_api.requests == []


def test_ingest_of_other_group_returns_404(
    client, mqtt_ingest, switch_to_other_group, db_api
):
    switch_to_other_group()

    response = client.get(f"/ingest/{mqtt_ingest['id']}/journal")

    assert response.status_code == 404
    assert db_api.requests == []


def test_db_api_error_returns_502(client, mqtt_ingest, db_api):
    db_api.stub_thing(mqtt_ingest["uuid"], "journal", status_code=500)

    response = client.get(f"/ingest/{mqtt_ingest['id']}/journal")

    assert response.status_code == 502


def test_db_api_not_configured_returns_503(client, mqtt_ingest, db_api_unconfigured):
    response = client.get(f"/ingest/{mqtt_ingest['id']}/journal")

    assert response.status_code == 503
