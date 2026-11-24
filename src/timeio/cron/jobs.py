"""Job catalog, command building and crontab rendering."""

from __future__ import annotations

import uuid as uuid_lib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from timeio.cron.schedule import MAX_JITTER_SECONDS, validate_expression

SCRIPT = "/scripts/mqtt_sync_wrapper.py"

JOB_TYPES = ("resync_thing", "sync_sms", "mqtt_monitoring")
SMS_ORIGINS = ("sms_backend", "sms_cv")
DEFAULT_RESYNC_DAYS = 7


def validate_params(job_type: str, params: dict[str, Any] | None) -> dict[str, Any]:
    """Return the normalized params for `job_type` or raise ValueError."""
    params = params or {}
    if job_type == "resync_thing":
        days = params.get("days", DEFAULT_RESYNC_DAYS)
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 365:
            raise ValueError(f"days must be an integer in 1..365, got {days!r}")
        return {"days": days}
    if job_type == "sync_sms":
        origin = params.get("origin")
        if origin not in SMS_ORIGINS:
            raise ValueError(f"origin must be one of {SMS_ORIGINS}, got {origin!r}")
        return {"origin": origin}
    if job_type == "mqtt_monitoring":
        if params:
            raise ValueError(f"mqtt_monitoring takes no params, got {params!r}")
        return {}
    raise ValueError(f"unknown job type {job_type!r}")


def build_command(
    job_type: str,
    target_uuid: str | None,
    params: dict[str, Any] | None,
    jitter: int,
) -> str:
    """Build the shell command of a job. Pseudo type `sync_thing` is the regular
    per-thing sync of `ingest_schedule`. Raises ValueError on invalid input.
    """
    if not 0 <= jitter <= MAX_JITTER_SECONDS:
        raise ValueError(f"jitter must be in 0..{MAX_JITTER_SECONDS}, got {jitter!r}")
    if job_type == "sync_sms":
        args = f"sync-sms {validate_params(job_type, params)['origin']}"
    elif job_type == "mqtt_monitoring":
        validate_params(job_type, params)
        args = "mqtt-monitoring"
    elif job_type in ("sync_thing", "resync_thing"):
        target = str(uuid_lib.UUID(str(target_uuid)))
        if job_type == "sync_thing":
            args = f"sync-thing {target}"
        else:
            days = validate_params(job_type, params)["days"]
            args = f"resync-range {target} --days {days}"
    else:
        raise ValueError(f"unknown job type {job_type!r}")
    return f"sleep {jitter} && python3 {SCRIPT} {args} > $STDOUT 2> $STDERR"


@dataclass
class ScheduleRow:
    ingest_id: int
    uuid: str
    name: str
    project: str
    cron_expression: str
    jitter_seconds: int
    enabled: bool
    updated_at: datetime


@dataclass
class JobRow:
    id: int
    job_type: str
    target_uuid: str | None
    target_name: str | None
    params: dict[str, Any]
    cron_expression: str
    jitter_seconds: int
    enabled: bool
    note: str | None
    updated_at: datetime


def _clean(value: object) -> str:
    return " ".join(str(value).split())


def _stamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _line(expression: str, command: str, enabled: bool) -> str:
    return f"{'' if enabled else '# '}{expression} {command}"


def render_crontab(
    schedules: list[ScheduleRow],
    jobs: list[JobRow],
    on_skip: Callable[[str], None] | None = None,
) -> str:
    """Render the complete crontab. Invalid rows are left out and reported
    via `on_skip`. The output is a pure function of the input."""

    def skip(msg: str) -> None:
        if on_skip is not None:
            on_skip(msg)

    out: list[str] = []
    for s in sorted(schedules, key=lambda r: r.ingest_id):
        expression = " ".join(s.cron_expression.split())
        try:
            if not validate_expression(expression):
                raise ValueError(f"invalid cron expression {s.cron_expression!r}")
            command = build_command("sync_thing", s.uuid, None, s.jitter_seconds)
        except ValueError as e:
            skip(f"ingest_schedule thing {s.uuid}: {e}")
            continue
        out.append(
            f"# {_stamp(s.updated_at)} | {_clean(s.project)} | {_clean(s.name)} | {s.uuid}\n"
            + _line(expression, command, s.enabled)
        )

    for j in sorted(jobs, key=lambda r: r.id):
        expression = " ".join(j.cron_expression.split())
        try:
            if not validate_expression(expression, allow_seconds=True):
                raise ValueError(f"invalid cron expression {j.cron_expression!r}")
            if j.job_type not in JOB_TYPES:
                raise ValueError(f"unknown job type {j.job_type!r}")
            if not isinstance(j.params, dict):
                raise ValueError("params must be a JSON object")
            command = build_command(
                j.job_type, j.target_uuid, j.params, j.jitter_seconds
            )
        except ValueError as e:
            skip(f"scheduled_job {j.id} ({j.job_type}): {e}")
            continue
        target = _clean(j.target_name or j.params.get("origin") or "")
        out.append(
            f"# {_stamp(j.updated_at)} | {j.job_type} | {target} | {_clean(j.note or '')}\n"
            + _line(expression, command, j.enabled)
        )

    # blank line between entries for readability
    return "\n\n".join(out) + "\n"
