from __future__ import annotations

import logging
import re
import uuid as uuid_lib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from random import randint
from typing import Any, Callable

import psycopg
from crontab import CronItem, CronRange, CronSlices
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

logger = logging.getLogger("cron")

SCHEMA = "dsm_db"
SCRIPT = "/scripts/mqtt_sync_wrapper.py"

MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 60 * 24
MINUTES_PER_WEEK = 60 * 24 * 7

# Random per-job start delay (seconds) prepended to the sync command to spread
# out jobs that share the same minute
SYNC_JITTER_SECONDS = 30
MAX_JITTER_SECONDS = 59
CONNECT_TIMEOUT = 10

JOB_TYPES = ("sync_thing", "resync_thing", "resync_project", "sync_sms")
SMS_ORIGINS = ("sms_backend", "sms_cv")
DEFAULT_RESYNC_DAYS = 7


# ---------------------------------------------------------------------------
# Schedule generation (expression strings)
# ---------------------------------------------------------------------------


def new_base_minute(interval: int) -> int:
    if interval == 0:
        return 0
    if 30 < interval < 60:
        # If for example the interval is 40min, we need to ensure
        # it can run twice an hour and therefor the start minute
        # must be lower than 20.
        return randint(0, 60 % interval - 1)
    return randint(0, min(interval - 1, 59))


def new_base_hour(interval: int) -> int:
    if interval < MINUTES_PER_HOUR:
        return 0
    return randint(0, min(interval // MINUTES_PER_HOUR - 1, 23))


def new_base_dom(interval: int) -> int:
    if interval < 2 * MINUTES_PER_DAY:
        return 1
    return randint(1, min(interval // MINUTES_PER_DAY - 1, 28))


def new_schedule(interval: int) -> str:
    """Creates a new schedule with a random start point to avoid that
    all jobs run at the same time.
    """
    interval = adjust_interval(_orig := interval)
    if _orig != interval:
        logger.info(f"adjusted interval form {_orig} minutes to {interval} minutes")

    start_m = new_base_minute(interval)
    if interval < MINUTES_PER_HOUR:
        step_m = interval
        return f"{start_m}-59/{step_m} * * * *"

    start_h = new_base_hour(interval)
    if interval < MINUTES_PER_DAY:
        start_h = new_base_hour(interval)
        step_h = interval // MINUTES_PER_HOUR
        return f"{start_m} {start_h}-23/{step_h} * * *"

    elif interval == MINUTES_PER_WEEK:
        day_of_week = randint(0, 6)
        return f"{start_m} {start_h} * * {day_of_week}"

    # interval is larger than a day but not weekly
    else:
        start_dom = new_base_dom(interval)
        step_day = interval // MINUTES_PER_DAY
        return f"{start_m} {start_h} {start_dom}-31/{step_day} * *"


def get_current_interval(expression: str) -> int:
    """Get interval in minutes from a cron expression"""
    item = CronItem()
    item.setall(expression)
    schedule = item.schedule(datetime(2020, 1, 1, 23, 59, 59))
    # avoid to have one value in the last hour and one in the next,
    # therefore we avoid schedule.get_prev()
    next_run = schedule.get_next()
    after_next_run = schedule.get_next()
    return int((after_next_run - next_run).total_seconds() / 60)


def adjust_interval(interval: int) -> int:
    """Adjust the interval to a value we can process cleanly in a cron schedule."""
    if interval == 0:
        return 1

    # We adjust the interval to proper divisor of 60.
    if interval <= MINUTES_PER_HOUR:
        divisors = [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60]
        return max(d for d in divisors if d <= interval)

    # We adjust the interval to an exact hourly value which
    # also is a proper divisor of 24h (1,2,3,4,6,8,12,24).
    elif interval <= MINUTES_PER_DAY:
        divisors = [60, 120, 180, 240, 360, 480, 720, 1440]
        return max(d for d in divisors if d <= interval)

    # We adjust the interval to exactly a 7-day value if it's close.
    elif MINUTES_PER_WEEK <= interval < MINUTES_PER_DAY * 8:
        return MINUTES_PER_WEEK

    # We adjust the interval to an exact daily value.
    return (interval // MINUTES_PER_DAY) * MINUTES_PER_DAY


def extract_base_minute(expression: str) -> int | None:
    """Extract the minute value from the cron expression.
    Returns the first numeric start value.
    """
    # if we have a list of expressions like 1,2,4-59/5
    # we extract the base minute only from the first one.
    minutes = CronSlices(expression)[0].parts[0]
    if isinstance(minutes, int):
        return minutes
    assert isinstance(minutes, CronRange)
    return minutes.vfrom


def extract_base_hour(expression: str) -> int | None:
    """Extract the hour value from the cron expression.
    Returns the first numeric start value.
    """
    # If we have a list of expressions like 1,2,4-23/5
    # we extract the base hour only from the first one.
    hour = CronSlices(expression)[1].parts[0]
    if isinstance(hour, int):
        return hour
    assert isinstance(hour, CronRange)
    return hour.vfrom


def update_cron_expression(expression: str, interval: int) -> str:
    """Update cron while keeping the same base minute for consistency.
    If the existing schedule already encodes the requested periodicity
    (produced by `new_schedule`, e.g. contains '/{step}', range-with-step
    or a matching comma-list for minutes), return the original string unchanged.
    """
    interval = adjust_interval(_orig := interval)
    if _orig != interval:
        logger.info(f"adjusted interval form {_orig} minutes to {interval} minutes")

    current_interval = get_current_interval(expression)
    if current_interval == interval:
        return str(CronSlices(expression))

    base_minute = extract_base_minute(expression)
    base_hour = extract_base_hour(expression)

    if interval < MINUTES_PER_HOUR:
        if base_minute >= interval:
            base_minute = new_base_minute(interval)
        return f"{base_minute}-59/{interval} * * * *"

    elif interval < MINUTES_PER_DAY:
        hour_step = interval // 60
        return f"{base_minute} */{hour_step} * * *"

    elif interval == MINUTES_PER_WEEK:
        dow = randint(0, 6)
        return f"{base_minute} {base_hour} * * {dow}"

    else:  # new_interval > DAY_MINUTES
        day_step = interval // (60 * 24)
        return f"{base_minute} {base_hour} */{day_step} * *"


# ---------------------------------------------------------------------------
# Validation and command building
# ---------------------------------------------------------------------------


def validate_expression(expression: str) -> bool:
    """Exactly 5 fields and valid for python-crontab."""
    return len(expression.split()) == 5 and CronSlices.is_valid(expression)


def validate_params(job_type: str, params: dict[str, Any] | None) -> dict[str, Any]:
    """Return the normalized params for `job_type` or raise ValueError."""
    params = params or {}
    if job_type == "sync_thing":
        return {}
    if job_type in ("resync_thing", "resync_project"):
        days = params.get("days", DEFAULT_RESYNC_DAYS)
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 365:
            raise ValueError(f"days must be an integer in 1..365, got {days!r}")
        return {"days": days}
    if job_type == "sync_sms":
        origin = params.get("origin")
        if origin not in SMS_ORIGINS:
            raise ValueError(f"origin must be one of {SMS_ORIGINS}, got {origin!r}")
        return {"origin": origin}
    raise ValueError(f"unknown job type {job_type!r}")


def build_command(
    job_type: str,
    target_uuid: str | None,
    params: dict[str, Any] | None,
    jitter: int,
) -> str:
    """Build the shell command of a job. Job type `sync_thing` is also used for
    the regular per-thing sync of `ingest_schedule`. Raises ValueError on invalid input.
    """
    if not 0 <= jitter <= MAX_JITTER_SECONDS:
        raise ValueError(f"jitter must be in 0..{MAX_JITTER_SECONDS}, got {jitter!r}")
    if job_type == "sync_sms":
        args = f"sync-sms {validate_params(job_type, params)['origin']}"
    elif job_type in ("sync_thing", "resync_thing", "resync_project"):
        target = str(uuid_lib.UUID(str(target_uuid)))
        if job_type == "sync_thing":
            args = f"sync-thing {target}"
        else:
            days = validate_params(job_type, params)["days"]
            cmd = "resync-range" if job_type == "resync_thing" else "resync-project"
            args = f"{cmd} {target} --days {days}"
    else:
        raise ValueError(f"unknown job type {job_type!r}")
    return f"sleep {jitter} && python3 {SCRIPT} {args} > $STDOUT 2> $STDERR"


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


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
    static_text: str = "",
    on_skip: Callable[[str], None] | None = None,
) -> str:
    """Render the complete crontab. Invalid rows are left out and reported
    via `on_skip`. The output is a pure function of the input."""

    def skip(msg: str) -> None:
        if on_skip is not None:
            on_skip(msg)

    out: list[str] = []
    if static_text.strip():
        out += [static_text.rstrip("\n"), ""]

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
            f"# {_stamp(s.updated_at)} | {_clean(s.project)} | {_clean(s.name)} | {s.uuid}"
        )
        out.append(_line(expression, command, s.enabled))

    for j in sorted(jobs, key=lambda r: r.id):
        expression = " ".join(j.cron_expression.split())
        try:
            if not validate_expression(expression):
                raise ValueError(f"invalid cron expression {j.cron_expression!r}")
            if not isinstance(j.params, dict):
                raise ValueError("params must be a JSON object")
            command = build_command(
                j.job_type, j.target_uuid, j.params, j.jitter_seconds
            )
        except ValueError as e:
            skip(f"custom_job {j.id} ({j.job_type}): {e}")
            continue
        target = _clean(j.target_name or j.params.get("origin") or "")
        out.append(
            f"# {_stamp(j.updated_at)} | {j.job_type} | {target} | {_clean(j.note or '')}"
        )
        out.append(_line(expression, command, j.enabled))

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Legacy crontab.txt parsing
# ---------------------------------------------------------------------------

_LEGACY_JOB_RE = re.compile(
    r"""^(?P<comment>\#\s*)?
        (?P<fields>(?:\S+\s+){4,6}\S+?)\s+
        (?:sleep\s+(?P<sleep>\d+)\s+&&\s+)?
        python3\s+/scripts/mqtt_sync_wrapper\.py\s+
        (?P<cmd>sync-thing|resync-range|sync-sms|mqtt-monitoring)
        (?P<args>(?:\s+[^\s>]+)*)
        (?:\s*>.*)?$""",
    re.VERBOSE,
)
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)


@dataclass
class LegacyJob:
    kind: str  # sync_thing | resync_thing | sync_sms | mqtt_monitoring
    target: str | None  # thing uuid or sms origin
    days: int | None
    expression: str
    jitter: int
    enabled: bool
    line_no: int


@dataclass
class LegacyCrontab:
    jobs: list[LegacyJob] = field(default_factory=list)
    unknown: list[tuple[int, str]] = field(default_factory=list)


_KINDS = {
    "sync-thing": "sync_thing",
    "resync-range": "resync_thing",
    "sync-sms": "sync_sms",
    "mqtt-monitoring": "mqtt_monitoring",
}


def parse_legacy_crontab(text: str) -> LegacyCrontab:
    """Line-wise parse of an old crontab.txt. Lines that are neither a known
    job nor a comment/blank end up in `unknown`."""
    result = LegacyCrontab()
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        m = _LEGACY_JOB_RE.match(line)
        if m is None:
            if not line.startswith("#"):
                result.unknown.append((line_no, line))
            continue
        kind = _KINDS[m["cmd"]]
        fields = m["fields"].split()
        args = m["args"].split()
        if kind == "mqtt_monitoring":
            result.jobs.append(
                LegacyJob(kind, None, None, " ".join(fields[:5]), 0, not m["comment"], line_no)  # fmt: skip
            )
            continue
        parsed = _parse_legacy_args(kind, args)
        # only plain 5-field jobs with exactly the known arguments can be represented
        if parsed is None or len(fields) != 5 or not validate_expression(m["fields"]):
            result.unknown.append((line_no, line))
            continue
        target, days = parsed
        result.jobs.append(
            LegacyJob(
                kind,
                target,
                days,
                " ".join(fields),
                min(int(m["sleep"] or 0), MAX_JITTER_SECONDS),
                not m["comment"],
                line_no,
            )
        )
    return result


def _parse_legacy_args(kind: str, args: list[str]) -> tuple[str, int | None] | None:
    """Return (target, days) if `args` has exactly the expected shape."""
    if kind == "sync_sms":
        return (args[0], None) if len(args) == 1 and args[0] in SMS_ORIGINS else None
    if not args or not _is_uuid(args[0]):
        return None
    target, rest = args[0].lower(), args[1:]
    if kind == "sync_thing":
        return (target, None) if not rest else None
    if not rest:
        return target, DEFAULT_RESYNC_DAYS
    if len(rest) == 2 and rest[0] == "--days":
        value = rest[1]
    elif len(rest) == 1 and rest[0].startswith("--days="):
        value = rest[0].removeprefix("--days=")
    else:
        return None
    if not value.isdigit() or not 1 <= int(value) <= 365:
        return None
    return target, int(value)


def _is_uuid(value: str | None) -> bool:
    return value is not None and _UUID_RE.match(value) is not None


def jitter_from_command(command: str) -> int | None:
    """Return the sleep offset of a sync command or None if it has none."""
    m = re.match(r"^\s*sleep\s+(\d+)\s+&&", command)
    return min(int(m[1]), MAX_JITTER_SECONDS) if m else None


# ---------------------------------------------------------------------------
# Database access (DSM DB)
# ---------------------------------------------------------------------------


def upsert_schedule(
    conn: psycopg.Connection,
    ingest_id: int,
    expression: str,
    jitter: int,
    enabled: bool,
) -> None:
    # updated_at only changes on real changes to avoid needless scheduler reloads
    conn.execute(
        f"""
        INSERT INTO {SCHEMA}.ingest_schedule
            (ingest_id, cron_expression, jitter_seconds, enabled)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (ingest_id) DO UPDATE SET
            cron_expression = EXCLUDED.cron_expression,
            jitter_seconds = EXCLUDED.jitter_seconds,
            enabled = EXCLUDED.enabled,
            updated_at = now()
        WHERE (ingest_schedule.cron_expression, ingest_schedule.jitter_seconds,
               ingest_schedule.enabled)
            IS DISTINCT FROM
              (EXCLUDED.cron_expression, EXCLUDED.jitter_seconds, EXCLUDED.enabled)
        """,
        (ingest_id, expression, jitter, enabled),
    )


def delete_schedule(conn: psycopg.Connection, ingest_id: int) -> None:
    conn.execute(
        f"DELETE FROM {SCHEMA}.ingest_schedule WHERE ingest_id = %s", (ingest_id,)
    )


def fetch_schedule(conn: psycopg.Connection, ingest_id: int) -> tuple[str, int] | None:
    """Return (cron_expression, jitter_seconds) of a thing, if scheduled."""
    row = conn.execute(
        f"SELECT cron_expression, jitter_seconds FROM {SCHEMA}.ingest_schedule "
        "WHERE ingest_id = %s",
        (ingest_id,),
    ).fetchone()
    return (row[0], row[1]) if row else None


def fetch_schedules(conn: psycopg.Connection) -> list[ScheduleRow]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"""
            SELECT s.ingest_id, i.uuid::text AS uuid, i.name, p.name AS project,
                   s.cron_expression, s.jitter_seconds, s.enabled, s.updated_at
            FROM {SCHEMA}.ingest_schedule s
            JOIN {SCHEMA}.ingest i ON i.id = s.ingest_id
            JOIN {SCHEMA}.permission_group p ON p.id = i.permission_group_id
            ORDER BY s.ingest_id
            """)
        return [ScheduleRow(**r) for r in cur.fetchall()]


def fetch_jobs(conn: psycopg.Connection) -> list[JobRow]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"""
            SELECT j.id, j.job_type,
                   COALESCE(i.uuid, p.uuid)::text AS target_uuid,
                   COALESCE(i.name, p.name) AS target_name,
                   j.params, j.cron_expression, j.jitter_seconds, j.enabled,
                   j.note, j.updated_at
            FROM {SCHEMA}.custom_job j
            LEFT JOIN {SCHEMA}.ingest i ON i.id = j.ingest_id
            LEFT JOIN {SCHEMA}.permission_group p ON p.id = j.permission_group_id
            ORDER BY j.id
            """)
        return [JobRow(**r) for r in cur.fetchall()]


def insert_job(
    conn: psycopg.Connection,
    job_type: str,
    cron_expression: str,
    jitter: int,
    params: dict[str, Any],
    ingest_id: int | None = None,
    permission_group_id: int | None = None,
    enabled: bool = True,
    note: str | None = None,
) -> int:
    row = conn.execute(
        f"""
        INSERT INTO {SCHEMA}.custom_job
            (job_type, ingest_id, permission_group_id, params, cron_expression,
             jitter_seconds, enabled, note)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            job_type,
            ingest_id,
            permission_group_id,
            Jsonb(params),
            cron_expression,
            jitter,
            enabled,
            note,
        ),
    ).fetchone()
    return row[0]


# ---------------------------------------------------------------------------
# Backfill from the legacy crontab.txt
# ---------------------------------------------------------------------------


@dataclass
class BackfillSummary:
    imported: int = 0
    skipped: int = 0
    orphaned: int = 0
    unknown: int = 0

    def __str__(self) -> str:
        return (
            f"imported={self.imported} skipped={self.skipped} "
            f"orphaned={self.orphaned} unknown={self.unknown}"
        )


def backfill_from_file(path: str | Path, dsn: str) -> BackfillSummary | None:
    """Import schedules from the legacy crontab.txt into the DSM DB.

    `sync-thing` lines are upserted into `ingest_schedule` (the file wins).
    `resync-range`/`sync-sms` lines go to `custom_job` but only while that
    table is empty, so later consolidations are not overwritten at each start.
    Returns None if the file or the tables do not exist (yet).
    """
    try:
        text = Path(path).read_text()
    except FileNotFoundError:
        logger.warning(f"backfill: {path} does not exist, skipping")
        return None
    legacy = parse_legacy_crontab(text)
    summary = BackfillSummary(unknown=len(legacy.unknown))
    for line_no, line in legacy.unknown:
        logger.warning(f"backfill: unknown crontab line {line_no}: {line}")

    try:
        with psycopg.connect(dsn, connect_timeout=CONNECT_TIMEOUT) as conn:
            ids = {
                r[0]: r[1]
                for r in conn.execute(f"SELECT uuid::text, id FROM {SCHEMA}.ingest")
            }
            seen: dict[str, LegacyJob] = {}
            for job in legacy.jobs:
                if job.kind != "sync_thing":
                    continue
                prev = seen.get(job.target)
                if prev is None or (job.enabled and not prev.enabled):
                    seen[job.target] = job
            n_sync = sum(1 for j in legacy.jobs if j.kind == "sync_thing")
            summary.skipped += n_sync - len(seen)
            for uuid, job in seen.items():
                if uuid not in ids:
                    logger.warning(f"backfill: orphaned sync-thing job for {uuid}")
                    summary.orphaned += 1
                    continue
                upsert_schedule(
                    conn, ids[uuid], job.expression, job.jitter, job.enabled
                )
                summary.imported += 1

            others = [j for j in legacy.jobs if j.kind in ("resync_thing", "sync_sms")]
            (count,) = conn.execute(
                f"SELECT count(*) FROM {SCHEMA}.custom_job"
            ).fetchone()
            if count:
                summary.skipped += len(others)
            else:
                for job in others:
                    _backfill_job(conn, job, ids, summary)
    except psycopg.errors.UndefinedTable:
        logger.warning("backfill: cron tables do not exist yet, skipping")
        return None

    logger.info(f"backfill from {path}: {summary}")
    return summary


def _backfill_job(
    conn: psycopg.Connection,
    job: LegacyJob,
    ids: dict[str, int],
    summary: BackfillSummary,
) -> None:
    note = f"imported from crontab.txt (line {job.line_no})"
    if job.kind == "sync_sms":
        insert_job(
            conn,
            "sync_sms",
            job.expression,
            job.jitter,
            {"origin": job.target},
            enabled=job.enabled,
            note=note,
        )
    else:
        if job.target not in ids:
            logger.warning(f"backfill: orphaned resync-range job for {job.target}")
            summary.orphaned += 1
            return
        insert_job(
            conn,
            "resync_thing",
            job.expression,
            job.jitter,
            {"days": job.days},
            ingest_id=ids[job.target],
            enabled=job.enabled,
            note=note,
        )
    summary.imported += 1
