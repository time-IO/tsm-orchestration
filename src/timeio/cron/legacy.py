"""One-time import of the legacy crontab.txt into the DSM DB."""

from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import psycopg

from timeio.cron import db
from timeio.cron.jobs import DEFAULT_RESYNC_DAYS, SMS_ORIGINS
from timeio.cron.schedule import MAX_JITTER_SECONDS, validate_expression

logger = logging.getLogger("cron")

BACKUP_SUFFIX = ".pre-db.bkp"

# prod lines vary: optional python3, optional .py, optional sleep, 5 or 7 fields
_LEGACY_JOB_RE = re.compile(
    r"""^(?P<comment>\#\s*)?
        (?P<fields>(?:(?!python3\s|sleep\s)\S+\s+){4,6}(?!python3\s|sleep\s)\S+)\s+
        (?:sleep\s+(?P<sleep>\d+)\s+&&\s+)?
        (?:python3\s+)?/scripts/mqtt_sync_wrapper(?:\.py)?\s+
        (?P<cmd>sync-thing|resync-range|sync-sms|mqtt-monitoring)
        (?P<args>(?:\s+(?!\d>)[^\s>]+)*)
        (?:\s*\d?>.*)?$""",
    re.VERBOSE,
)
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)

_KINDS = {
    "sync-thing": "sync_thing",
    "resync-range": "resync_thing",
    "sync-sms": "sync_sms",
    "mqtt-monitoring": "mqtt_monitoring",
}


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


@dataclass
class ImportSummary:
    imported: int = 0
    skipped: int = 0
    orphaned: int = 0
    unknown: int = 0

    def __str__(self) -> str:
        return (
            f"imported={self.imported} skipped={self.skipped} "
            f"orphaned={self.orphaned} unknown={self.unknown}"
        )


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
        expression = " ".join(fields)
        jitter = min(int(m["sleep"] or 0), MAX_JITTER_SECONDS)
        enabled = not m["comment"]
        if kind == "mqtt_monitoring":
            if m["args"].split() or not validate_expression(expression, True):
                result.unknown.append((line_no, line))
                continue
            result.jobs.append(
                LegacyJob(kind, None, None, expression, jitter, enabled, line_no)
            )
            continue
        parsed = _parse_legacy_args(kind, m["args"].split())
        # only plain 5-field jobs with exactly the known arguments can be represented
        if parsed is None or not validate_expression(expression):
            result.unknown.append((line_no, line))
            continue
        target, days = parsed
        result.jobs.append(
            LegacyJob(kind, target, days, expression, jitter, enabled, line_no)
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


def backup_legacy(path: Path) -> Path:
    """Copy `path` once to `<path>.pre-db.bkp`; never overwrites. Raises OSError."""
    backup = path.with_name(path.name + BACKUP_SUFFIX)
    if not backup.exists():
        tmp = backup.with_name(backup.name + ".tmp")
        shutil.copy2(path, tmp)
        tmp.replace(backup)
        logger.info(f"backed up {path} to {backup}")
    return backup


def _ingests(conn: psycopg.Connection, uuids: list[str]) -> dict[str, tuple]:
    """uuid -> (ingest_id, configured sync interval or None)."""
    rows = conn.execute(
        f"""
        SELECT i.uuid::text, i.id,
               COALESCE(s.sync_interval_in_minutes, a.sync_interval_in_minutes)
        FROM {db.SCHEMA}.ingest i
        LEFT JOIN {db.SCHEMA}.ingest_external_sftp s ON s.ingest_id = i.id
        LEFT JOIN {db.SCHEMA}.ingest_external_api a ON a.ingest_id = i.id
        WHERE i.uuid = ANY(%s::uuid[])
        """,
        (uuids,),
    ).fetchall()
    return {r[0]: (r[1], r[2]) for r in rows}


def import_legacy(conn: psycopg.Connection, text: str) -> ImportSummary:
    """Import a legacy crontab in one transaction and set the import marker.
    Existing rows win; nothing is updated."""
    parsed = parse_legacy_crontab(text)
    summary = ImportSummary(unknown=len(parsed.unknown))
    for line_no, line in parsed.unknown:
        logger.warning(f"legacy crontab line {line_no} not imported: {line}")
    with conn.transaction():
        if db.is_imported(conn):
            raise RuntimeError("legacy crontab was already imported")
        uuids = sorted({j.target for j in parsed.jobs if _is_uuid(j.target)})
        ingests = _ingests(conn, uuids)
        for job in parsed.jobs:
            ingest_id, interval = ingests.get(job.target, (None, None))
            if job.kind in ("sync_thing", "resync_thing") and ingest_id is None:
                summary.orphaned += 1
                logger.warning(
                    f"legacy crontab line {job.line_no}: unknown thing {job.target}"
                )
                continue
            if _import_job(conn, job, ingest_id, interval):
                summary.imported += 1
            else:
                summary.skipped += 1
        db.mark_imported(conn)
    return summary


def _import_job(
    conn: psycopg.Connection, job: LegacyJob, ingest_id: int | None, interval
) -> bool:
    if job.kind == "sync_thing":
        cur = conn.execute(
            f"""
            INSERT INTO {db.SCHEMA}.ingest_schedule
                (ingest_id, cron_expression, jitter_seconds, enabled,
                 sync_interval_minutes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ingest_id) DO NOTHING
            """,
            (ingest_id, job.expression, job.jitter, job.enabled, interval),
        )
        return cur.rowcount == 1
    if job.kind == "resync_thing":
        params = {"days": job.days}
    elif job.kind == "sync_sms":
        params = {"origin": job.target}
    else:
        params = {}
    if db.job_exists(conn, job.kind, params, ingest_id, job.expression):
        return False
    db.insert_job(
        conn,
        job.kind,
        job.expression,
        job.jitter,
        params,
        ingest_id=ingest_id,
        enabled=job.enabled,
        note=f"imported from crontab.txt line {job.line_no}",
    )
    return True
