"""
Integration tests for the ingest/external-api/neutron-monitor router.

Unlike the unit tests, these tests use a real database connection.
Each test creates data via the API, verifies it, and cleans up after
itself. This tests the full stack: router -> repository -> database.
"""

import uuid
import pytest
from main import app
from sqlmodel import Session, text
from dependencies import engine, get_current_user
from tests.utils.user_proxy import UserProxy
from models import User

BASE_PATH = "/ingest/external-api/neutron-monitor"


@pytest.fixture
def nm_station(base_data):
    """Creates a neutron_monitor_station row required as FK for
    ingest_external_api_neutron_monitor.station_id. Cleaned up after
    the test (after ingest rows, due to FK)."""
    station_uuid = str(uuid.uuid4())
    station_id_str = f"test-station-{station_uuid}"
    with Session(engine) as session:
        session.exec(
            text("""
                INSERT INTO neutron_monitor_station (station_id, description)
                VALUES (:station_id, 'Test Station')
            """),
            params={"station_id": station_id_str},
        )
        session.commit()

        station_id = session.exec(
            text(
                "SELECT id FROM neutron_monitor_station WHERE station_id = :station_id"
            ),
            params={"station_id": station_id_str},
        ).scalar_one()

    yield station_id

    # Delete ingests first, then station
    with Session(engine) as session:
        session.exec(
            text(
                "DELETE FROM ingest_external_api_neutron_monitor WHERE ingest_id IN (SELECT id FROM ingest WHERE permission_group_id = :pg_id)"
            ),
            params={"pg_id": base_data["permission_group_id"]},
        )
        session.exec(
            text(
                "DELETE FROM ingest_external_api WHERE ingest_id IN (SELECT id FROM ingest WHERE permission_group_id = :pg_id)"
            ),
            params={"pg_id": base_data["permission_group_id"]},
        )
        session.exec(
            text("DELETE FROM ingest WHERE permission_group_id = :pg_id"),
            params={"pg_id": base_data["permission_group_id"]},
        )
        session.exec(
            text("DELETE FROM neutron_monitor_station WHERE id = :id"),
            params={"id": station_id},
        )
        session.commit()


def _nm_payload(base_data, station_id, **overrides):
    payload = {
        "name": "Integration Test Neutron Monitor",
        "permission_group_id": base_data["permission_group_id"],
        "sync_enabled": True,
        "sync_interval_in_minutes": 15,
        "station_id": station_id,
        "time_resolution_in_minutes": 60,
    }
    payload.update(overrides)
    return payload


def test_create_and_read(client, base_data, nm_station):
    payload = _nm_payload(base_data, nm_station)
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    created = response.json()
    assert created["name"] == "Integration Test Neutron Monitor"
    assert created["station_id"] == nm_station
    assert created["api_type"] == "nm"
    ingest_id = created["id"]

    # read back
    response = client.get(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 200
    assert response.json()["id"] == ingest_id


def test_create_and_update(client, base_data, nm_station):
    payload = _nm_payload(base_data, nm_station, name="Nm To Update")
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    ingest_id = response.json()["id"]

    response = client.patch(
        f"{BASE_PATH}/{ingest_id}", json={"time_resolution_in_minutes": 30}
    )
    assert response.status_code == 200
    assert response.json()["time_resolution_in_minutes"] == 30


def test_create_and_delete(client, base_data, nm_station):
    payload = _nm_payload(base_data, nm_station, name="Nm To Delete")
    response = client.post(f"{BASE_PATH}/", json=payload)
    assert response.status_code == 200
    ingest_id = response.json()["id"]

    response = client.delete(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    response = client.get(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 404


def test_read_list(client, base_data, nm_station):
    for name in ["Nm List A", "Nm List B"]:
        client.post(f"{BASE_PATH}/", json=_nm_payload(base_data, nm_station, name=name))

    response = client.get(f"{BASE_PATH}/")
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_read_not_found(client):
    response = client.get(f"{BASE_PATH}/99999")
    assert response.status_code == 404


def test_read_list_unauthenticated(client_no_auth):
    response = client_no_auth.get(f"{BASE_PATH}/")
    assert response.status_code == 401


def test_read_one_unauthenticated(client_no_auth):
    response = client_no_auth.get(f"{BASE_PATH}/1")
    assert response.status_code == 401


def test_create_unauthenticated(client_no_auth, base_data, nm_station):
    response = client_no_auth.post(
        f"{BASE_PATH}/", json=_nm_payload(base_data, nm_station)
    )
    assert response.status_code == 401


def test_read_list_wrong_group_returns_empty(
    client, client_other_group, base_data, nm_station
):
    client.post(f"{BASE_PATH}/", json=_nm_payload(base_data, nm_station))

    response = client_other_group.get(f"{BASE_PATH}/")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_read_one_wrong_group_returns_404(
    client, base_data, other_group_data, nm_station
):
    created_response = client.post(
        f"{BASE_PATH}/", json=_nm_payload(base_data, nm_station)
    )
    assert created_response.status_code == 200
    ingest_id = created_response.json()["id"]

    with Session(engine) as s:
        other_user = s.get(User, other_group_data["user_id"])
        proxy = UserProxy(other_user, [other_group_data["permission_group_id"]])
    app.dependency_overrides[get_current_user] = lambda: proxy

    response = client.get(f"{BASE_PATH}/{ingest_id}")
    assert response.status_code == 404
