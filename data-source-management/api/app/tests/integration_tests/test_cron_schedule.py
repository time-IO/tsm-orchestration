"""Integration tests for the cron schedule tables (cascades and CHECKs)."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from dependencies import engine
from models import (
    Ingest,
    IngestSchedule,
    QualityControlSetting,
    ScheduledJob,
)


@pytest.fixture
def cleanup_jobs():
    yield
    with Session(engine) as session:
        for job in session.exec(select(ScheduledJob)).all():
            session.delete(job)
        session.commit()


def _ingest(session: Session, mqtt_ingest) -> Ingest:
    return session.exec(
        select(Ingest).where(Ingest.uuid == uuid.UUID(mqtt_ingest["uuid"]))
    ).one()


def test_ingest_delete_cascades(mqtt_ingest, cleanup_jobs):
    with Session(engine) as session:
        ingest = _ingest(session, mqtt_ingest)
        ingest_id = ingest.id
        schedule = IngestSchedule(ingest_id=ingest_id, cron_expression="0 * * * *")
        session.add(schedule)
        session.add(
            ScheduledJob(
                job_type="resync_thing",
                ingest_id=ingest_id,
                params={"days": 8},
                cron_expression="0 4 * * MON",
            )
        )
        sms = ScheduledJob(
            job_type="sync_sms",
            params={"origin": "sms_backend"},
            cron_expression="*/5 * * * *",
        )
        session.add(sms)
        session.commit()
        sms_id = sms.id
        session.refresh(schedule)
        assert schedule.sync_interval_minutes is None
        session.delete(ingest)
        session.commit()
        assert session.get(IngestSchedule, ingest_id) is None
        assert not session.exec(
            select(ScheduledJob).where(ScheduledJob.ingest_id == ingest_id)
        ).all()
        assert session.get(ScheduledJob, sms_id) is not None


def test_scheduled_job_defaults(cleanup_jobs):
    with Session(engine) as session:
        job = ScheduledJob(
            job_type="mqtt_monitoring", cron_expression="*/30 * * * * * *"
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        assert (job.params, job.jitter_seconds, job.enabled) == ({}, 0, True)


@pytest.mark.parametrize(
    "kwargs, with_ingest",
    [
        ({"job_type": "resync_thing"}, False),
        ({"job_type": "sync_sms"}, True),
        ({"job_type": "mqtt_monitoring"}, True),
        ({"job_type": "sync_sms", "jitter_seconds": 60}, False),
        ({"job_type": "resync_project"}, False),
        ({"job_type": "sync_thing"}, True),
        ({"job_type": "bogus"}, False),
    ],
)
def test_scheduled_job_checks(kwargs, with_ingest, mqtt_ingest, cleanup_jobs):
    with Session(engine) as session:
        ingest_id = _ingest(session, mqtt_ingest).id if with_ingest else None
        session.add(
            ScheduledJob(cron_expression="0 * * * *", ingest_id=ingest_id, **kwargs)
        )
        with pytest.raises(IntegrityError):
            session.commit()


def _qc_setting(session: Session, base_data) -> int:
    qc = QualityControlSetting(
        permission_group_id=base_data["permission_group_id"],
        name="Scheduled QC",
        context_window="1h",
    )
    session.add(qc)
    session.commit()
    return qc.id


def test_trigger_qc_cascades_on_qc_setting_delete(base_data, cleanup_qc, cleanup_jobs):
    with Session(engine) as session:
        qc_id = _qc_setting(session, base_data)
        job = ScheduledJob(
            job_type="trigger_qc",
            quality_control_setting_id=qc_id,
            params={"interval": "1h"},
            cron_expression="0 * * * *",
        )
        session.add(job)
        session.commit()
        job_id = job.id
        session.delete(session.get(QualityControlSetting, qc_id))
        session.commit()
        assert session.get(ScheduledJob, job_id) is None


@pytest.mark.parametrize(
    ("job_type", "with_qc"), [("trigger_qc", False), ("sync_sms", True)]
)
def test_scheduled_job_qc_setting_check(
    job_type, with_qc, base_data, cleanup_qc, cleanup_jobs
):
    with Session(engine) as session:
        qc_id = _qc_setting(session, base_data) if with_qc else None
        session.add(
            ScheduledJob(
                job_type=job_type,
                quality_control_setting_id=qc_id,
                cron_expression="0 * * * *",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_enabled_ingest_schedule_needs_expression(mqtt_ingest):
    with Session(engine) as session:
        ingest_id = _ingest(session, mqtt_ingest).id
        session.add(IngestSchedule(ingest_id=ingest_id, enabled=True))
        with pytest.raises(IntegrityError):
            session.commit()
