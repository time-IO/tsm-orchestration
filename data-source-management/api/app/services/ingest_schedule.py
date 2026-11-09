from datetime import datetime, timedelta, timezone

from croniter import CroniterBadCronError, croniter

from models import (
    IngestSchedule,
    IngestScheduleInfoRead,
    IngestScheduleRead,
    CustomJob,
    CustomJobRead,
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


def _read(model, entry, now: datetime | None = None):
    runs = next_runs(
        entry.cron_expression, entry.jitter_seconds, entry.enabled, now=now
    )
    return model.model_validate(entry).model_copy(update={"next_runs": runs})


def build_custom_job_read(job: CustomJob, now: datetime | None = None) -> CustomJobRead:
    return _read(CustomJobRead, job, now)


def build_schedule_info(
    schedule: IngestSchedule | None,
    jobs: list[CustomJob],
    now: datetime | None = None,
) -> IngestScheduleInfoRead:
    return IngestScheduleInfoRead(
        schedule=_read(IngestScheduleRead, schedule, now) if schedule else None,
        jobs=[build_custom_job_read(j, now) for j in jobs],
    )
