"""Keeps `ingest_schedule` in line with an external ingest's sync settings."""

from datetime import datetime, timedelta, timezone
from random import randint
from typing import Optional

from croniter import CroniterBadCronError, croniter
from models import (
    Ingest,
    IngestExternalApi,
    IngestExternalSftp,
    IngestSchedule,
    ScheduledJob,
)
from models.ingest_schedule import IngestScheduleRead
from models.scheduled_job import IngestScheduleInfoRead, ScheduledJobRead
from timeio.cron.schedule import (
    SYNC_JITTER_SECONDS,
    new_schedule,
    normalize_expression,
    update_cron_expression,
)

NEXT_RUNS_COUNT = 5


def next_runs(
    expression: Optional[str],
    jitter_seconds: int,
    enabled: bool,
    count: int = NEXT_RUNS_COUNT,
    now: Optional[datetime] = None,
) -> list[datetime]:
    """Upcoming start times (UTC) including the start delay; empty if disabled."""
    if not enabled or not expression:
        return []
    expression = normalize_expression(expression)
    if len(expression.split()) != 5:
        return []
    now = now or datetime.now(timezone.utc)
    jitter = timedelta(seconds=jitter_seconds)
    try:
        # start before now so a run whose delay is still pending is listed
        it = croniter(expression, now - jitter)
        return [it.get_next(datetime) + jitter for _ in range(count)]
    except (CroniterBadCronError, ValueError, KeyError):
        return []


def _read_with_next_runs(entity, read_model):
    read = read_model.model_validate(entity, from_attributes=True)
    read.next_runs = next_runs(
        entity.cron_expression, entity.jitter_seconds, entity.enabled
    )
    return read


def build_schedule_info(
    schedule: Optional[IngestSchedule], jobs: list[ScheduledJob]
) -> IngestScheduleInfoRead:
    return IngestScheduleInfoRead(
        schedule=(
            _read_with_next_runs(schedule, IngestScheduleRead) if schedule else None
        ),
        jobs=[_read_with_next_runs(j, ScheduledJobRead) for j in jobs],
    )


def sync_ingest_schedule(
    ingest: Ingest, config: IngestExternalApi | IngestExternalSftp
) -> IngestSchedule:
    """Create/adapt the ingest's schedule; recompute only on interval change, keep jitter."""
    interval = config.sync_interval_in_minutes
    enabled = bool(config.sync_enabled) and interval is not None
    row = ingest.schedule

    if row is None:
        return IngestSchedule(
            ingest_id=ingest.id,
            cron_expression=new_schedule(interval) if interval is not None else None,
            jitter_seconds=randint(0, SYNC_JITTER_SECONDS),
            enabled=enabled,
            sync_interval_minutes=interval,
        )

    current = row.cron_expression and normalize_expression(row.cron_expression)
    expression = current
    if interval is not None and (
        current is None or interval != row.sync_interval_minutes
    ):
        expression = (
            update_cron_expression(current, interval)
            if current
            else new_schedule(interval)
        )
    # updated_at is rendered into the crontab, so only bump it on visible changes
    if (expression, enabled) != (row.cron_expression, row.enabled):
        row.cron_expression = expression
        row.enabled = enabled
        row.updated_at = datetime.now(timezone.utc)
    row.sync_interval_minutes = interval
    return row
