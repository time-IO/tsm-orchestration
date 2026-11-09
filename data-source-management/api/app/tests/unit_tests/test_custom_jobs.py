from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from dependencies import get_current_user, get_repo_ingest
from main import app
from models import CustomJob, User
from services import custom_jobs

TS = datetime(2026, 1, 1, tzinfo=timezone.utc)
URL = "/ingest/5/custom-jobs"


@pytest.fixture
def superuser(client):
    app.dependency_overrides[get_current_user] = lambda: User(
        id=9, is_superuser=True, permission_group_ids=[]
    )


@pytest.fixture
def repo(superuser, override_repo):
    repo = override_repo(get_repo_ingest)
    repo.find_one.return_value = MagicMock(id=5, ingest_type="external_api")

    def save(job):
        job.id = job.id or 1
        job.updated_at = TS
        return job

    repo.save_custom_job.side_effect = save
    return repo


def make_job(**kwargs):
    defaults = dict(
        id=3, job_type="resync_thing", ingest_id=5, params={"days": 7},
        cron_expression="0 3 * * 0", jitter_seconds=4, enabled=True,
        note=None, updated_at=TS,
    )  # fmt: skip
    return CustomJob(**{**defaults, **kwargs})


def test_non_superuser_is_forbidden(client, override_repo):
    override_repo(get_repo_ingest)
    assert client.get(f"{URL}/available").status_code == 403
    body = {"job_type": "sync_thing", "cron_expression": "0 * * * *"}
    assert client.post(URL, json=body).status_code == 403
    assert client.patch(f"{URL}/1", json={"enabled": False}).status_code == 403
    assert client.delete(f"{URL}/1").status_code == 403


@pytest.mark.parametrize(
    "ingest_type, expected",
    [
        ("external_api", ["sync_thing", "resync_thing"]),
        ("external_sftp", ["sync_thing"]),
        ("mqtt", []),
    ],
)
def test_available_by_ingest_type(client, repo, ingest_type, expected):
    repo.find_one.return_value = MagicMock(id=5, ingest_type=ingest_type)
    body = client.get(f"{URL}/available").json()
    assert [s["job_type"] for s in body] == expected


def test_create_fills_defaults(client, repo):
    response = client.post(
        URL,
        json={"job_type": "resync_thing", "cron_expression": " 0  3 * * 0 "},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["cron_expression"] == "0 3 * * 0"
    assert body["params"] == {"days": 7}
    assert body["ingest_id"] == 5
    assert 0 <= body["jitter_seconds"] <= custom_jobs.MAX_RANDOM_JITTER_SECONDS
    assert len(body["next_runs"]) == 5


@pytest.mark.parametrize(
    "payload",
    [
        {"job_type": "sync_thing", "cron_expression": "* * * *"},
        {"job_type": "sync_thing", "cron_expression": "@daily"},
        {"job_type": "sync_thing", "cron_expression": "0 0 * * MON"},
        {"job_type": "sync_thing", "cron_expression": "61 * * * *"},
        {"job_type": "resync_thing", "cron_expression": "0 * * * *", "params": {"days": 0}},
        {"job_type": "resync_thing", "cron_expression": "0 * * * *", "params": {"days": True}},
        {"job_type": "resync_thing", "cron_expression": "0 * * * *", "params": {"x": 1}},
        {"job_type": "sync_thing", "cron_expression": "0 * * * *", "jitter_seconds": 60},
        {"job_type": "resync_project", "cron_expression": "0 * * * *"},
        {"job_type": "bogus", "cron_expression": "0 * * * *"},
    ],
)  # fmt: skip
def test_create_rejects_invalid(client, repo, payload):
    assert client.post(URL, json=payload).status_code == 422
    repo.save_custom_job.assert_not_called()


def test_create_rejects_type_not_available_for_ingest(client, repo):
    repo.find_one.return_value = MagicMock(id=5, ingest_type="external_sftp")
    body = {"job_type": "resync_thing", "cron_expression": "0 * * * *"}
    assert client.post(URL, json=body).status_code == 422


def test_update_changes_only_given_fields(client, repo):
    repo.find_custom_job.return_value = make_job()
    response = client.patch(
        f"{URL}/3", json={"cron_expression": "30 4 * * 1", "enabled": None}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cron_expression"] == "30 4 * * 1"
    assert body["enabled"] is True
    assert body["params"] == {"days": 7}


def test_update_validates_params(client, repo):
    repo.find_custom_job.return_value = make_job()
    assert client.patch(f"{URL}/3", json={"params": {"days": 999}}).status_code == 422
    repo.save_custom_job.assert_not_called()


def test_delete(client, repo):
    job = make_job()
    repo.find_custom_job.return_value = job
    assert client.delete(f"{URL}/3").status_code == 204
    repo.delete_custom_job.assert_called_once_with(job)


def test_catalog_matches_db_constraint():
    assert {d.value for d in custom_jobs.CATALOG} <= {
        "sync_thing",
        "resync_thing",
    }
