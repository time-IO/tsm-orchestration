from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, Column, DateTime, text
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel
from sqlmodel import SQLModel, Field

from models.ingest_schedule import IngestScheduleRead


class ScheduledJob(SQLModel, table=True):
    """Manual and default cron jobs of fixed job types, see timeio.cron.jobs."""

    __tablename__ = "scheduled_job"

    __table_args__ = (
        CheckConstraint(
            "job_type IN ('resync_thing', 'sync_sms', 'mqtt_monitoring', 'trigger_qc')",
            name="ck_scheduled_job_type",
        ),
        CheckConstraint(
            "(job_type = 'resync_thing') = (ingest_id IS NOT NULL)",
            name="ck_scheduled_job_ingest",
        ),
        CheckConstraint(
            "(job_type = 'trigger_qc') = (quality_control_setting_id IS NOT NULL)",
            name="ck_scheduled_job_qc_setting",
        ),
        CheckConstraint(
            "jitter_seconds BETWEEN 0 AND 59", name="ck_scheduled_job_jitter"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    job_type: str
    ingest_id: Optional[int] = Field(
        default=None, foreign_key="ingest.id", ondelete="CASCADE"
    )
    quality_control_setting_id: Optional[int] = Field(
        default=None, foreign_key="quality_control_setting.id", ondelete="CASCADE"
    )
    params: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )
    cron_expression: str
    jitter_seconds: int = Field(default=0, sa_column_kwargs={"server_default": "0"})
    enabled: bool = Field(default=True, sa_column_kwargs={"server_default": "true"})
    note: Optional[str] = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=text("now()")
        ),
    )


class ScheduledJobRead(BaseModel):
    id: int
    job_type: str
    params: dict
    cron_expression: str
    jitter_seconds: int
    enabled: bool
    note: Optional[str]
    updated_at: datetime
    next_runs: list[datetime] = []


class IngestScheduleInfoRead(BaseModel):
    schedule: Optional[IngestScheduleRead] = None
    jobs: list[ScheduledJobRead] = []
