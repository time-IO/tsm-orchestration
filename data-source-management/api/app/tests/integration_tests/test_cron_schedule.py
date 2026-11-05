"""Integration tests for the cron schedule tables (cascades and CHECKs)."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from dependencies import engine
from models import Ingest, IngestSchedule, PermissionGroup, ScheduledJob


@pytest.fixture
def cleanup_jobs():
    yield
    with Session(engine) as session:
        for job in session.exec(select(ScheduledJob)).all():
            session.delete(job)
        session.commit()


def test_ingest_delete_cascades(mqtt_ingest, cleanup_jobs):
    with Session(engine) as session:
        ingest = session.exec(
            select(Ingest).where(Ingest.uuid == uuid.UUID(mqtt_ingest["uuid"]))
        ).one()
        ingest_id = ingest.id
        session.add(IngestSchedule(ingest_id=ingest_id, cron_expression="0 * * * *"))
        session.add(
            ScheduledJob(
                job_type="resync_thing",
                ingest_id=ingest_id,
                cron_expression="0 3 * * 0",
            )
        )
        session.commit()
        session.delete(ingest)
        session.commit()
        assert session.get(IngestSchedule, ingest_id) is None
        assert not session.exec(
            select(ScheduledJob).where(ScheduledJob.ingest_id == ingest_id)
        ).all()


def test_permission_group_delete_cascades(cleanup_jobs):
    with Session(engine) as session:
        pg = PermissionGroup(
            name=f"CronGroup-{uuid.uuid4()}",
            uuid=uuid.uuid4(),
            entitlement=f"urn:test:group:{uuid.uuid4()}",
        )
        session.add(pg)
        session.flush()
        pg_id = pg.id
        session.add(
            ScheduledJob(
                job_type="resync_project",
                permission_group_id=pg_id,
                cron_expression="0 3 * * 0",
            )
        )
        session.commit()
        session.delete(pg)
        session.commit()
        assert not session.exec(
            select(ScheduledJob).where(ScheduledJob.permission_group_id == pg_id)
        ).all()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"job_type": "resync_thing"},
        {"job_type": "resync_project"},
        {"job_type": "sync_sms", "jitter_seconds": 60},
    ],
)
def test_scheduled_job_checks(kwargs, cleanup_jobs):
    with Session(engine) as session:
        session.add(ScheduledJob(cron_expression="0 * * * *", **kwargs))
        with pytest.raises(IntegrityError):
            session.commit()


def test_schedule_endpoint(client, mqtt_ingest, cleanup_jobs, base_data):
    with Session(engine) as session:
        ingest = session.exec(
            select(Ingest).where(Ingest.uuid == uuid.UUID(mqtt_ingest["uuid"]))
        ).one()
        session.add(IngestSchedule(ingest_id=ingest.id, cron_expression="5 * * * *"))
        session.add(
            ScheduledJob(
                job_type="resync_project",
                permission_group_id=base_data["permission_group_id"],
                cron_expression="0 3 * * 0",
            )
        )
        session.commit()
        ingest_id = ingest.id

    body = client.get(f"/ingest/{ingest_id}/schedule").json()
    assert body["schedule"]["cron_expression"] == "5 * * * *"
    assert [j["scope"] for j in body["jobs"]] == ["project"]
