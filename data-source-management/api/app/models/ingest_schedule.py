from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import CheckConstraint, Column, DateTime, text
from sqlmodel import SQLModel, Field


class IngestSchedule(SQLModel, table=True):
    """Sync schedule per ingest, written by worker-thing-setup, read by cron-scheduler."""

    __tablename__ = "ingest_schedule"

    __table_args__ = (
        CheckConstraint(
            "jitter_seconds BETWEEN 0 AND 59", name="ck_ingest_schedule_jitter"
        ),
    )

    ingest_id: int = Field(
        foreign_key="ingest.id", primary_key=True, ondelete="CASCADE"
    )
    cron_expression: str
    jitter_seconds: int = Field(default=0, sa_column_kwargs={"server_default": "0"})
    enabled: bool = Field(default=True, sa_column_kwargs={"server_default": "true"})
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=text("now()")
        ),
    )


class IngestScheduleRead(BaseModel):
    cron_expression: str
    jitter_seconds: int
    enabled: bool
    updated_at: datetime
    next_runs: list[datetime]
