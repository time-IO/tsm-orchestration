from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, text
from sqlmodel import SQLModel, Field


class CronLegacyImport(SQLModel, table=True):
    """Single-row marker: the legacy crontab.txt was imported by cron-scheduler."""

    __tablename__ = "cron_legacy_import"

    __table_args__ = (CheckConstraint("id", name="ck_cron_legacy_import_single_row"),)

    id: bool = Field(
        default=True, primary_key=True, sa_column_kwargs={"server_default": "true"}
    )
    imported_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=text("now()")
        ),
    )
