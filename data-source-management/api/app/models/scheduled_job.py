from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, Column, DateTime, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


class ScheduledJob(SQLModel, table=True):
    """Manual and default cron jobs of fixed job types, see timeio.cron."""

    __tablename__ = "scheduled_job"

    __table_args__ = (
        CheckConstraint(
            "job_type IN ('resync_thing', 'sync_sms', 'mqtt_monitoring')",
            name="ck_scheduled_job_type",
        ),
        CheckConstraint(
            "(job_type = 'resync_thing') = (ingest_id IS NOT NULL)",
            name="ck_scheduled_job_ingest",
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
