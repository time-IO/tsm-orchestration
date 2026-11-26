"""Integration tests: external ingest create/update keeps ingest_schedule in line."""

from datetime import datetime, timezone

import pytest
from sqlmodel import Session

from dependencies import engine, get_current_user
from main import app
from models import IngestSchedule, ScheduledJob, User
from services.ingest_schedule import next_runs
from timeio.cron.schedule import get_current_interval

from .test_ingest_external_api_bosch import _bosch_payload
from .test_ingest_external_api_dwd import _dwd_payload
from .test_ingest_external_api_neutron_monitor import _nm_payload, nm_station
from .test_ingest_external_api_sensoto import _sensoto_payload
from .test_ingest_external_api_the_things_network import _ttn_payload
from .test_ingest_external_api_tsystems import _tsystems_payload
from .test_ingest_external_api_uba import _uba_payload
from .test_ingest_external_api_zentra import _zentra_payload
from .test_ingest_external_sftp import _sftp_payload
from ..utils.user_proxy import UserProxy

SFTP = "/ingest/external-sftp"

PATHS = {
    "external-sftp": _sftp_payload,
    "external-api/bosch": _bosch_payload,
    "external-api/dwd": _dwd_payload,
    "external-api/neutron-monitor": _nm_payload,
    "external-api/sensoto": _sensoto_payload,
    "external-api/the-things-network": _ttn_payload,
    "external-api/tsystems": _tsystems_payload,
    "external-api/uba": _uba_payload,
    "external-api/zentra": _zentra_payload,
}


@pytest.fixture(autouse=True)
def _cleanup(cleanup_ingest):
    yield


def _row(ingest_id) -> IngestSchedule | None:
    with Session(engine) as session:
        return session.get(IngestSchedule, ingest_id)


def _set_row(ingest_id, **values):
    with Session(engine) as session:
        row = session.get(IngestSchedule, ingest_id)
        row.sqlmodel_update(values)
        session.add(row)
        session.commit()


def _create_sftp(client, base_data, **overrides) -> int:
    response = client.post(f"{SFTP}/", json=_sftp_payload(base_data, **overrides))
    assert response.status_code == 200
    return response.json()["id"]


def _patch_sftp(client, ingest_id, **data):
    response = client.patch(f"{SFTP}/{ingest_id}", json=data)
    assert response.status_code == 200


@pytest.mark.parametrize("path", PATHS)
def test_every_path_writes_schedule(client, base_data, request, path):
    make = PATHS[path]
    if path == "external-api/neutron-monitor":
        payload = make(base_data, request.getfixturevalue("nm_station"))
    else:
        payload = make(base_data)
    response = client.post(f"/ingest/{path}/", json=payload)
    assert response.status_code == 200
    created = response.json()
    ingest_id = created["id"]

    row = _row(ingest_id)
    interval = created["sync_interval_in_minutes"]
    if interval is None:
        assert (row.cron_expression, row.enabled) == (None, False)
    assert row.sync_interval_minutes == interval
    assert row.enabled is (created["sync_enabled"] and interval is not None)
    assert 0 <= row.jitter_seconds <= 30
    jitter = row.jitter_seconds

    response = client.patch(
        f"/ingest/{path}/{ingest_id}", json={"sync_interval_in_minutes": 30}
    )
    assert response.status_code == 200
    # tsystems and uba keep their fixed 60 min interval
    interval = response.json()["sync_interval_in_minutes"]
    row = _row(ingest_id)
    assert row.sync_interval_minutes == interval
    assert get_current_interval(row.cron_expression) == interval
    assert row.jitter_seconds == jitter


def test_unrelated_edit_keeps_row(client, base_data):
    ingest_id = _create_sftp(client, base_data, sync_interval_in_minutes=20)
    _set_row(ingest_id, cron_expression="5,35,50 * * * *", jitter_seconds=42)
    before = _row(ingest_id)

    _patch_sftp(client, ingest_id, path="/other", sync_interval_in_minutes=20)

    after = _row(ingest_id)
    assert (after.cron_expression, after.jitter_seconds) == ("5,35,50 * * * *", 42)
    assert after.updated_at == before.updated_at


def test_interval_change_keeps_base_minute_and_jitter(client, base_data):
    ingest_id = _create_sftp(client, base_data, sync_interval_in_minutes=60)
    _set_row(ingest_id, cron_expression="17 */1 * * *", jitter_seconds=42)

    _patch_sftp(client, ingest_id, sync_interval_in_minutes=120)

    row = _row(ingest_id)
    assert row.cron_expression == "17 */2 * * *"
    assert (row.jitter_seconds, row.sync_interval_minutes) == (42, 120)


@pytest.mark.parametrize(
    ("stored", "interval", "expected"),
    [
        ("0 * * * *", 90, "0 * * * *"),  # adjusted to 60, used to store @hourly
        ("@hourly", 90, "0 * * * *"),
        ("@daily", 1440, "0 0 * * *"),
        ("@daily", 120, "0 */2 * * *"),
    ],
)
def test_interval_change_never_stores_macro(
    client, base_data, stored, interval, expected
):
    ingest_id = _create_sftp(client, base_data, sync_interval_in_minutes=20)
    _set_row(ingest_id, cron_expression=stored)

    _patch_sftp(client, ingest_id, sync_interval_in_minutes=interval)

    row = _row(ingest_id)
    assert row.cron_expression == expected
    assert next_runs(row.cron_expression, 0, True)


def test_sync_enabled_toggle(client, base_data):
    ingest_id = _create_sftp(client, base_data)
    expression = _row(ingest_id).cron_expression

    _patch_sftp(client, ingest_id, sync_enabled=False)
    row = _row(ingest_id)
    assert (row.enabled, row.cron_expression) == (False, expression)

    _patch_sftp(client, ingest_id, sync_enabled=True)
    assert _row(ingest_id).enabled is True


def test_null_interval(client, base_data):
    ingest_id = _create_sftp(client, base_data, sync_interval_in_minutes=None)
    row = _row(ingest_id)
    assert (row.enabled, row.cron_expression, row.sync_interval_minutes) == (
        False,
        None,
        None,
    )
    jitter = row.jitter_seconds

    _patch_sftp(client, ingest_id, sync_interval_in_minutes=60)
    row = _row(ingest_id)
    assert row.enabled and get_current_interval(row.cron_expression) == 60
    assert row.jitter_seconds == jitter
    _set_row(ingest_id, cron_expression="17 */1 * * *", jitter_seconds=42)

    _patch_sftp(client, ingest_id, sync_interval_in_minutes=None)
    row = _row(ingest_id)
    assert (row.enabled, row.cron_expression, row.sync_interval_minutes) == (
        False,
        "17 */1 * * *",
        None,
    )

    _patch_sftp(client, ingest_id, sync_interval_in_minutes=120)
    row = _row(ingest_id)
    assert (row.enabled, row.cron_expression, row.jitter_seconds) == (
        True,
        "17 */2 * * *",
        42,
    )


def test_delete_removes_schedule(client, base_data):
    ingest_id = _create_sftp(client, base_data)
    assert _row(ingest_id) is not None
    assert client.delete(f"{SFTP}/{ingest_id}").status_code == 200
    assert _row(ingest_id) is None


def test_schedule_endpoint(client, base_data):
    ingest_id = _create_sftp(client, base_data, sync_interval_in_minutes=60)
    with Session(engine) as session:
        session.add(
            ScheduledJob(
                job_type="resync_thing",
                ingest_id=ingest_id,
                params={"days": 8},
                cron_expression="0 4 * * MON",
                note="weekly",
            )
        )
        session.commit()

    response = client.get(f"/ingest/{ingest_id}/schedule")
    assert response.status_code == 200
    body = response.json()
    row = _row(ingest_id)
    assert body["schedule"]["cron_expression"] == row.cron_expression
    assert body["schedule"]["jitter_seconds"] == row.jitter_seconds
    assert body["schedule"]["sync_interval_minutes"] == 60
    assert body["schedule"]["enabled"] is True
    assert [(j["job_type"], j["params"], j["note"]) for j in body["jobs"]] == [
        ("resync_thing", {"days": 8}, "weekly")
    ]
    assert len(body["schedule"]["next_runs"]) == 5
    assert len(body["jobs"][0]["next_runs"]) == 5


def test_schedule_endpoint_without_schedule(client, mqtt_ingest):
    response = client.get(f"/ingest/{mqtt_ingest['id']}/schedule")
    assert response.status_code == 200
    assert response.json() == {"schedule": None, "jobs": []}


def test_schedule_endpoint_access_scope(client, base_data, other_group_data):
    ingest_id = _create_sftp(client, base_data)
    with Session(engine) as session:
        other_user = session.get(User, other_group_data["user_id"])
        proxy = UserProxy(other_user, [other_group_data["permission_group_id"]])
    app.dependency_overrides[get_current_user] = lambda: proxy

    response = client.get(f"/ingest/{ingest_id}/schedule")
    assert response.status_code == 404


def _utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("now", "first"),
    [
        (_utc(2026, 1, 1, 10, 0), _utc(2026, 1, 1, 10, 17, 30)),
        # the 10:17 run is still waiting for its start delay
        (_utc(2026, 1, 1, 10, 17, 10), _utc(2026, 1, 1, 10, 17, 30)),
        (_utc(2026, 1, 1, 10, 17, 40), _utc(2026, 1, 1, 12, 17, 30)),
    ],
)
def test_next_runs(now, first):
    runs = next_runs("17 */2 * * *", 30, True, now=now)
    assert runs[0] == first
    assert [(b - a).total_seconds() for a, b in zip(runs, runs[1:])] == [7200] * 4


@pytest.mark.parametrize(
    ("expression", "enabled"),
    [("17 */2 * * *", False), ("*/30 * * * * * *", True), ("nope", True)],
)
def test_next_runs_empty(expression, enabled):
    assert next_runs(expression, 0, enabled) == []


def test_next_runs_day_names():
    runs = next_runs("0 4 * * MON", 0, True, count=2, now=_utc(2026, 11, 24))
    assert runs == [_utc(2026, 11, 30, 4), _utc(2026, 12, 7, 4)]
