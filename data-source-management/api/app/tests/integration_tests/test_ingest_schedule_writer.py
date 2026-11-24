"""Integration tests: external ingest create/update keeps ingest_schedule in line."""

import pytest
from sqlmodel import Session

from dependencies import engine
from models import IngestSchedule
from timeio.cron.schedule import extract_base_minute, get_current_interval

from .test_ingest_external_api_bosch import _bosch_payload
from .test_ingest_external_api_dwd import _dwd_payload
from .test_ingest_external_api_neutron_monitor import _nm_payload, nm_station
from .test_ingest_external_api_sensoto import _sensoto_payload
from .test_ingest_external_api_the_things_network import _ttn_payload
from .test_ingest_external_api_tsystems import _tsystems_payload
from .test_ingest_external_api_uba import _uba_payload
from .test_ingest_external_api_zentra import _zentra_payload
from .test_ingest_external_sftp import _sftp_payload

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
        assert row is None
        return
    assert row.sync_interval_minutes == interval
    assert row.enabled is created["sync_enabled"]
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


def test_unrelated_edit_keeps_hand_tuned_row(client, base_data):
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
    assert _row(ingest_id) is None

    _patch_sftp(client, ingest_id, sync_interval_in_minutes=60)
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
