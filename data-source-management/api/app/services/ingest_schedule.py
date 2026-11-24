"""Keeps `ingest_schedule` in line with an external ingest's sync settings."""

from datetime import datetime, timezone
from random import randint
from typing import Optional

from sqlmodel import Session

from models import IngestExternalApi, IngestExternalSftp, IngestSchedule
from timeio.cron.schedule import (
    SYNC_JITTER_SECONDS,
    new_schedule,
    update_cron_expression,
)


def _sync_config(
    session: Session, ingest_id: int
) -> Optional[tuple[Optional[int], bool]]:
    for model in (IngestExternalSftp, IngestExternalApi):
        config = session.get(model, ingest_id)
        if config is not None:
            return config.sync_interval_in_minutes, bool(config.sync_enabled)
    return None


def apply_ingest_schedule(session: Session, ingest_id: int) -> None:
    """Create/adapt the row; recompute only on interval change, keep jitter. No commit."""
    session.flush()
    config = _sync_config(session, ingest_id)
    if config is None:
        return
    interval, sync_enabled = config
    enabled = sync_enabled and interval is not None
    row = session.get(IngestSchedule, ingest_id)

    if row is None:
        if interval is not None:
            session.add(
                IngestSchedule(
                    ingest_id=ingest_id,
                    cron_expression=new_schedule(interval),
                    jitter_seconds=randint(0, SYNC_JITTER_SECONDS),
                    enabled=enabled,
                    sync_interval_minutes=interval,
                )
            )
        return

    expression = row.cron_expression
    if interval is not None and interval != row.sync_interval_minutes:
        expression = update_cron_expression(row.cron_expression, interval)
    # updated_at is rendered into the crontab, so only bump it on visible changes
    if (expression, enabled) != (row.cron_expression, row.enabled):
        row.cron_expression = expression
        row.enabled = enabled
        row.updated_at = datetime.now(timezone.utc)
    row.sync_interval_minutes = interval
    session.add(row)
