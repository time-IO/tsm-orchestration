"""One-time import of the legacy crontab.txt into the DSM DB."""

from __future__ import annotations

import logging
import re
import shlex
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import psycopg

from timeio.cron import db
from timeio.cron.jobs import DEFAULT_RESYNC_DAYS, QC_INTERVAL_RE, SMS_ORIGINS
from timeio.cron.schedule import (
    MACROS,
    MAX_JITTER_SECONDS,
    normalize_expression,
    validate_expression,
)

logger = logging.getLogger("cron")

BACKUP_SUFFIX = ".pre-db.bkp"

# prod lines vary: optional python3, optional .py, optional sleep, 5/7 fields or @macro
_LEGACY_JOB_RE = re.compile(
    r"""^(?P<comment>\#\s*)?
        (?P<fields>@\w+|(?:(?!python3\s|sleep\s)\S+\s+){4,6}(?!python3\s|sleep\s)\S+)\s+
        (?:sleep\s+(?P<sleep>\d+)\s+&&\s+)?
        (?:python3\s+)?/scripts/mqtt_sync_wrapper(?:\.py)?\s+
        (?P<cmd>sync-thing|resync-range|sync-sms|mqtt-monitoring)
        (?P<args>(?:\s+(?!\d>)[^\s>]+)*)
        (?:\s*\d?>.*)?$""",
    re.VERBOSE,
)
# trigger_qaqc.py --interval 1h --project-uuid <group uuid> --qc-settings-name <name>
_LEGACY_QC_RE = re.compile(
    r"""^(?P<comment>\#\s*)?
        (?P<fields>@\w+|(?:(?!python3\s|sleep\s)\S+\s+){4,6}(?!python3\s|sleep\s)\S+)\s+
        (?:sleep\s+(?P<sleep>\d+)\s+&&\s+)?
        (?:python3\s+)?/scripts/trigger_qaqc(?:\.py)?
        (?P<args>(?:\s+.*?)?)
        (?:\s+\d?>.*)?$""",
    re.VERBOSE,
)
_QC_OPTIONS = {"--interval", "--project-uuid", "--qc-settings-name"}
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
    kind: str  # sync_thing | resync_thing | sync_sms | mqtt_monitoring | trigger_qc
    target: str | None  # thing uuid, sms origin or permission group uuid
    days: int | None
    expression: str
    jitter: int
    enabled: bool
    line_no: int
    qc_name: str | None = None
    qc_interval: str | None = None


@dataclass
class LegacyCrontab:
    jobs: list[LegacyJob] = field(default_factory=list)
    unknown: list[tuple[int, str]] = field(default_factory=list)


class ImportBlocked(RuntimeError):
    """The legacy crontab has active lines the import would drop."""


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


def _is_commented_job(line: str) -> bool:
    """True for a commented-out cron line, not for a plain comment."""
    fields = line.lstrip("#").split()
    if len(fields) > 1 and fields[0].lower() in MACROS:
        return True
    return (len(fields) > 5 and validate_expression(" ".join(fields[:5]))) or (
        len(fields) > 7 and validate_expression(" ".join(fields[:7]), True)
    )


def parse_legacy_crontab(text: str) -> LegacyCrontab:
    """Line-wise parse of an old crontab.txt. Lines that are neither a known
    job nor a comment/blank end up in `unknown`."""
    result = LegacyCrontab()
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if (qc := _parse_legacy_qc(line, line_no)) is not None:
            result.jobs.append(qc)
            continue
        m = _LEGACY_JOB_RE.match(line)
        if m is None:
            if not line.startswith("#") or _is_commented_job(line):
                result.unknown.append((line_no, line))
            continue
        kind = _KINDS[m["cmd"]]
        expression = normalize_expression(m["fields"])
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


def _parse_legacy_qc(line: str, line_no: int) -> LegacyJob | None:
    """A trigger_qaqc.py line with exactly the three known options, else None."""
    m = _LEGACY_QC_RE.match(line)
    if m is None:
        return None
    expression = normalize_expression(m["fields"])
    try:
        tokens = shlex.split(m["args"])
    except ValueError:
        return None
    options = {}
    while tokens:
        key, _, value = tokens.pop(0).partition("=")
        if key not in _QC_OPTIONS or key in options:
            return None
        if not value:
            if not tokens:
                return None
            value = tokens.pop(0)
        options[key] = value
    if (
        options.keys() != _QC_OPTIONS
        or not QC_INTERVAL_RE.match(options["--interval"])
        or not _is_uuid(options["--project-uuid"])
        or not validate_expression(expression, allow_seconds=True)
    ):
        return None
    return LegacyJob(
        "trigger_qc",
        options["--project-uuid"].lower(),
        None,
        expression,
        min(int(m["sleep"] or 0), MAX_JITTER_SECONDS),
        not m["comment"],
        line_no,
        qc_name=options["--qc-settings-name"],
        qc_interval=options["--interval"],
    )


def _qc_setting_id(conn: psycopg.Connection, group_uuid: str, name: str) -> int | None:
    row = conn.execute(
        f"""
        SELECT q.id FROM {db.SCHEMA}.quality_control_setting q
        JOIN {db.SCHEMA}.permission_group g ON g.id = q.permission_group_id
        WHERE g.uuid::text = %s AND lower(q.name) = lower(%s)
        """,
        (group_uuid, name),
    ).fetchone()
    return row[0] if row else None


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
    selected, duplicates, conflicts = _select_jobs(parsed.jobs)
    active_unknown = [(n, line) for n, line in parsed.unknown if line[0] != "#"]
    if active_unknown or conflicts:
        problems = [
            f"line {n} cannot be imported: {line}" for n, line in active_unknown
        ]
        raise ImportBlocked(
            "; ".join(problems + conflicts)
            + " -- comment out the lines to drop in the legacy crontab"
        )
    summary = ImportSummary(unknown=len(parsed.unknown), skipped=len(duplicates))
    for line_no, line in parsed.unknown:
        logger.warning(f"legacy crontab line {line_no} not imported: {line}")
    for job, kept in duplicates:
        logger.warning(
            f"legacy crontab line {job.line_no} duplicates line {kept.line_no}, "
            "not imported"
        )
    with conn.transaction():
        if db.is_imported(conn):
            raise RuntimeError("legacy crontab was already imported")
        uuids = sorted(
            {j.target for j in selected if j.kind in ("sync_thing", "resync_thing")}
        )
        ingests = _ingests(conn, uuids)
        for job in selected:
            if job.kind == "trigger_qc":
                qc_id = _qc_setting_id(conn, job.target, job.qc_name)
                if qc_id is None:
                    summary.orphaned += 1
                    logger.warning(
                        f"legacy crontab line {job.line_no}: unknown QC settings "
                        f"{job.qc_name!r} in project {job.target}"
                    )
                elif _import_qc_job(conn, job, qc_id):
                    summary.imported += 1
                else:
                    summary.skipped += 1
                continue
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


def _job_key(job: LegacyJob) -> tuple:
    """Lines with the same key would end up as one DB row."""
    if job.kind == "sync_thing":
        return job.kind, job.target
    qc_name = job.qc_name.lower() if job.qc_name else None
    return job.kind, job.target, job.days, qc_name, job.qc_interval, job.expression


def _select_jobs(
    jobs: list[LegacyJob],
) -> tuple[list[LegacyJob], list[tuple[LegacyJob, LegacyJob]], list[str]]:
    """One job per key: the last active line, else the last line.
    Returns (selected, (dropped, kept) pairs, conflicts)."""
    groups: dict[tuple, list[LegacyJob]] = {}
    for job in jobs:
        groups.setdefault(_job_key(job), []).append(job)
    selected, duplicates, conflicts = [], [], []
    for group in groups.values():
        active = [j for j in group if j.enabled]
        if len({j.expression for j in active}) > 1:
            lines = ", ".join(str(j.line_no) for j in active)
            conflicts.append(
                f"lines {lines} are active with different schedules for {group[0].target}"
            )
        kept = (active or group)[-1]
        selected.append(kept)
        duplicates += [(j, kept) for j in group if j is not kept]
    selected.sort(key=lambda j: j.line_no)
    return selected, duplicates, conflicts


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


def _import_qc_job(conn: psycopg.Connection, job: LegacyJob, qc_id: int) -> bool:
    params = {"interval": job.qc_interval}
    if db.job_exists(conn, job.kind, params, None, job.expression, qc_id):
        return False
    db.insert_job(
        conn,
        job.kind,
        job.expression,
        job.jitter,
        params,
        enabled=job.enabled,
        note=f"imported from crontab.txt line {job.line_no}",
        qc_setting_id=qc_id,
    )
    return True
