from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, DateTime, text
from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .ingest import Ingest


class IngestSchedule(SQLModel, table=True):
    """Sync schedule of every external SFTP/API ingest, derived on each save, read by cron-scheduler."""

    __tablename__ = "ingest_schedule"

    __table_args__ = (
        CheckConstraint(
            "jitter_seconds BETWEEN 0 AND 59", name="ck_ingest_schedule_jitter"
        ),
        CheckConstraint(
            "NOT enabled OR cron_expression IS NOT NULL",
            name="ck_ingest_schedule_expression",
        ),
    )

    ingest_id: int = Field(
        foreign_key="ingest.id", primary_key=True, ondelete="CASCADE"
    )
    # NULL until the ingest gets a sync interval
    cron_expression: Optional[str] = None
    jitter_seconds: int = Field(default=0, sa_column_kwargs={"server_default": "0"})
    enabled: bool = Field(default=True, sa_column_kwargs={"server_default": "true"})
    # interval the expression was computed from; detects real interval changes
    sync_interval_minutes: Optional[int] = None
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=text("now()")
        ),
    )

    ingest: "Ingest" = Relationship(back_populates="schedule")


class IngestScheduleRead(BaseModel):
    # NULL until the ingest gets a sync interval
    cron_expression: Optional[str] = None
    jitter_seconds: int
    enabled: bool
    sync_interval_minutes: Optional[int]
    updated_at: datetime
    next_runs: list[datetime] = []
