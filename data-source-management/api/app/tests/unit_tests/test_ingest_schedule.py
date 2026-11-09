from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi import HTTPException

from dependencies import get_repo_ingest
from models import IngestSchedule, CustomJob
from services.ingest_schedule import build_schedule_info, next_runs

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
TS = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_next_runs_adds_jitter():
    runs = next_runs("0-59/10 * * * *", 7, True, count=3, now=NOW)
    assert [r.strftime("%H:%M:%S") for r in runs] == [
        "12:00:07",
        "12:10:07",
        "12:20:07",
    ]


def test_next_runs_includes_run_with_pending_jitter():
    now = datetime(2026, 1, 1, 12, 10, 3, tzinfo=timezone.utc)
    runs = next_runs("0-59/10 * * * *", 7, True, count=1, now=now)
    assert runs[0].strftime("%H:%M:%S") == "12:10:07"


def test_next_runs_disabled_or_invalid_is_empty():
    assert next_runs("*/5 * * * *", 0, False, now=NOW) == []
    assert next_runs("not a cron", 0, True, now=NOW) == []


def test_build_schedule_info():
    schedule = IngestSchedule(
        ingest_id=1,
        cron_expression="5 * * * *",
        jitter_seconds=3,
        enabled=True,
        updated_at=TS,
    )
    jobs = [
        CustomJob(
            id=1, job_type="resync_thing", ingest_id=1, params={"days": 7},
            cron_expression="0 3 * * 0", jitter_seconds=0, enabled=True, updated_at=TS,
        ),
        CustomJob(
            id=2, job_type="resync_project", permission_group_id=9, params={"days": 7},
            cron_expression="0 4 * * 0", jitter_seconds=0, enabled=False, updated_at=TS,
        ),
    ]  # fmt: skip
    info = build_schedule_info(schedule, jobs, now=NOW)
    assert info.schedule.next_runs[0].strftime("%H:%M:%S") == "12:05:03"
    assert [(j.job_type, len(j.next_runs)) for j in info.jobs] == [
        ("resync_thing", 5),
        ("resync_project", 0),
    ]


def test_endpoint_returns_schedule(client, override_repo):
    repo = override_repo(get_repo_ingest)
    repo.find_one.return_value = MagicMock()
    repo.find_schedule.return_value = IngestSchedule(
        ingest_id=1, cron_expression="5 * * * *", jitter_seconds=3,
        enabled=True, updated_at=TS,
    )  # fmt: skip
    repo.find_custom_jobs.return_value = []

    response = client.get("/ingest/1/schedule")

    assert response.status_code == 200
    body = response.json()
    assert body["schedule"]["cron_expression"] == "5 * * * *"
    assert len(body["schedule"]["next_runs"]) == 5 and body["jobs"] == []
    assert repo.find_one.call_args.kwargs["access_scope"] is not None


def test_endpoint_without_schedule(client, override_repo):
    repo = override_repo(get_repo_ingest)
    repo.find_schedule.return_value = None
    repo.find_custom_jobs.return_value = []
    response = client.get("/ingest/1/schedule")
    assert response.status_code == 200
    assert response.json() == {"schedule": None, "jobs": []}


def test_endpoint_without_access(client, override_repo):
    repo = override_repo(get_repo_ingest)
    repo.find_one.side_effect = HTTPException(status_code=404, detail="Not found")
    response = client.get("/ingest/1/schedule")
    assert response.status_code == 404
    repo.find_schedule.assert_not_called()
    repo.find_custom_jobs.assert_not_called()
