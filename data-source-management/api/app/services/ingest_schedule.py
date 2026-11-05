from datetime import datetime, timedelta, timezone

from croniter import CroniterBadCronError, croniter

from models import (
    IngestSchedule,
    IngestScheduleInfoRead,
    IngestScheduleRead,
    ScheduledJob,
    ScheduledJobRead,
)

NEXT_RUNS_COUNT = 5


def next_runs(
    expression: str,
    jitter_seconds: int,
    enabled: bool,
    count: int = NEXT_RUNS_COUNT,
    now: datetime | None = None,
) -> list[datetime]:
    """Upcoming start times (UTC) including the jitter delay of the job."""
    if not enabled:
        return []
    now = now or datetime.now(timezone.utc)
    jitter = timedelta(seconds=jitter_seconds)
    try:
        # start before now so a run whose jitter delay is still pending is listed
        it = croniter(expression, now - jitter)
        return [it.get_next(datetime) + jitter for _ in range(count)]
    except (CroniterBadCronError, ValueError, KeyError):
        return []


def build_schedule_info(
    schedule: IngestSchedule | None,
    jobs: list[ScheduledJob],
    now: datetime | None = None,
) -> IngestScheduleInfoRead:
    return IngestScheduleInfoRead(
        schedule=(
            IngestScheduleRead(
                cron_expression=schedule.cron_expression,
                jitter_seconds=schedule.jitter_seconds,
                enabled=schedule.enabled,
                updated_at=schedule.updated_at,
                next_runs=next_runs(
                    schedule.cron_expression,
                    schedule.jitter_seconds,
                    schedule.enabled,
                    now=now,
                ),
            )
            if schedule
            else None
        ),
        jobs=[
            ScheduledJobRead(
                id=j.id,
                job_type=j.job_type,
                scope="ingest" if j.ingest_id is not None else "project",
                params=j.params,
                cron_expression=j.cron_expression,
                jitter_seconds=j.jitter_seconds,
                enabled=j.enabled,
                note=j.note,
                updated_at=j.updated_at,
                next_runs=next_runs(
                    j.cron_expression, j.jitter_seconds, j.enabled, now=now
                ),
            )
            for j in jobs
        ],
    )
