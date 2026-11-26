"""DSM DB access for cron-scheduler and cron_jobs.py."""

from __future__ import annotations

import logging
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from timeio.cron.jobs import JobRow, ScheduleRow

logger = logging.getLogger("cron")

SCHEMA = "dsm_db"
CONNECT_TIMEOUT = 10

# (job_type, params, cron_expression); seeded when no row of that kind exists
DEFAULT_JOBS: tuple[tuple[str, dict[str, Any], str], ...] = (
    ("mqtt_monitoring", {}, "*/30 * * * * * *"),
    ("sync_sms", {"origin": "sms_backend"}, "*/5 * * * *"),
)


def connect(dsn: str) -> psycopg.Connection:
    # autocommit: each conn.transaction() commits on its own (import, seeding)
    return psycopg.connect(dsn, connect_timeout=CONNECT_TIMEOUT, autocommit=True)


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
                   COALESCE(i.uuid, g.uuid)::text AS target_uuid,
                   COALESCE(i.name, g.name || ' / ' || q.name) AS target_name,
                   j.params, j.cron_expression, j.jitter_seconds, j.enabled,
                   j.note, j.updated_at, q.name AS qc_settings_name
            FROM {SCHEMA}.scheduled_job j
            LEFT JOIN {SCHEMA}.ingest i ON i.id = j.ingest_id
            LEFT JOIN {SCHEMA}.quality_control_setting q
                ON q.id = j.quality_control_setting_id
            LEFT JOIN {SCHEMA}.permission_group g ON g.id = q.permission_group_id
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
    enabled: bool = True,
    note: str | None = None,
    qc_setting_id: int | None = None,
) -> int:
    row = conn.execute(
        f"""
        INSERT INTO {SCHEMA}.scheduled_job
            (job_type, ingest_id, params, cron_expression,
             jitter_seconds, enabled, note, quality_control_setting_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            job_type,
            ingest_id,
            Jsonb(params),
            cron_expression,
            jitter,
            enabled,
            note,
            qc_setting_id,
        ),
    ).fetchone()
    return row[0]


def job_exists(
    conn: psycopg.Connection,
    job_type: str,
    params: dict[str, Any],
    ingest_id: int | None = None,
    cron_expression: str | None = None,
    qc_setting_id: int | None = None,
) -> bool:
    """True if a job of `job_type` exists whose params contain `params` (and
    which matches `ingest_id`, `qc_setting_id` and, if given, `cron_expression`)."""
    row = conn.execute(
        f"""
        SELECT 1 FROM {SCHEMA}.scheduled_job
        WHERE job_type = %s AND params @> %s
          AND ingest_id IS NOT DISTINCT FROM %s
          AND quality_control_setting_id IS NOT DISTINCT FROM %s
          AND (%s::text IS NULL OR cron_expression = %s)
        LIMIT 1
        """,
        (
            job_type,
            Jsonb(params),
            ingest_id,
            qc_setting_id,
            cron_expression,
            cron_expression,
        ),
    ).fetchone()
    return row is not None


def seed_defaults(conn: psycopg.Connection) -> list[str]:
    """Insert missing default jobs; disabled ones count as present. Returns
    the job types inserted."""
    inserted = []
    with conn.transaction():
        for job_type, params, expression in DEFAULT_JOBS:
            if not job_exists(conn, job_type, params):
                insert_job(conn, job_type, expression, 0, params, note="default")
                inserted.append(job_type)
    return inserted


def tables_id(conn: psycopg.Connection) -> str:
    """Changes when the cron tables are recreated (Alembic downgrade + upgrade)."""
    row = conn.execute(f"SELECT '{SCHEMA}.ingest_schedule'::regclass::oid").fetchone()
    return str(row[0])
