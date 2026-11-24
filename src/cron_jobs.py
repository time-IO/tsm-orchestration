#!/usr/bin/env python3
"""Maintain the cron-scheduler's jobs (`dsm_db.scheduled_job`) and thing schedules
(`dsm_db.ingest_schedule`)."""

from __future__ import annotations

from random import randint

import click
import psycopg

from timeio.cron import db, jobs, schedule
from timeio.common import get_envvar


def _connect() -> psycopg.Connection:
    return db.connect(get_envvar("DSMDB_DSN"))


def _lookup(conn: psycopg.Connection, uuid: str) -> tuple[int, str]:
    row = conn.execute(
        f"SELECT id, name FROM {db.SCHEMA}.ingest WHERE uuid::text = %s", (uuid,)
    ).fetchone()
    if row is None:
        raise click.ClickException(f"No ingest found with uuid {uuid}")
    return row[0], row[1]


def _expression(expression: str, allow_seconds: bool) -> str:
    if not schedule.validate_expression(expression, allow_seconds=allow_seconds):
        raise click.BadParameter(f"invalid cron expression {expression!r}")
    return " ".join(expression.split())


def _jitter(jitter: int | None) -> int:
    return randint(0, schedule.SYNC_JITTER_SECONDS) if jitter is None else jitter


def _params(job_type: str, **params) -> dict:
    try:
        return jobs.validate_params(job_type, params)
    except ValueError as e:
        raise click.BadParameter(str(e))


def _common(f):
    f = click.option("--note", help="Who/why, shown in the crontab comment.")(f)
    f = click.option(
        "--jitter",
        type=click.IntRange(0, schedule.MAX_JITTER_SECONDS),
        help="Start delay in seconds, random 0-30 if omitted.",
    )(f)
    f = click.option(
        "--schedule",
        required=True,
        help="Cron expression, 5 fields or 7 fields (seconds first, year last).",
    )(f)
    return f


@click.group()
def cli():
    pass


@cli.command("list")
def list_jobs():
    """List the scheduled jobs."""
    with _connect() as conn:
        rows = db.fetch_jobs(conn)
    click.echo("id  type  target  schedule  jitter  enabled  note")
    for j in rows:
        target = j.target_name or j.params.get("origin") or "-"
        click.echo(
            f"{j.id}  {j.job_type}  {target}  {j.cron_expression}  {j.jitter_seconds}s  "
            f"{'yes' if j.enabled else 'no'}  {j.note or ''}"
        )


@cli.group()
def add():
    """Add a job."""


def _add(job_type, expression, jitter, params, note, ingest_id=None):
    expression = _expression(expression, allow_seconds=True)
    with _connect() as conn:
        job_id = db.insert_job(
            conn, job_type, expression, _jitter(jitter), params,
            ingest_id=ingest_id, note=note,
        )  # fmt: skip
    click.echo(f"Added job {job_id}")


@add.command("resync-thing")
@click.argument("thing_uuid")
@click.option("--days", default=jobs.DEFAULT_RESYNC_DAYS, show_default=True)
@_common
def add_resync_thing(thing_uuid, days, schedule, jitter, note):
    params = _params("resync_thing", days=days)
    _expression(schedule, allow_seconds=True)
    with _connect() as conn:
        ingest_id, name = _lookup(conn, thing_uuid)
        has_api = conn.execute(
            f"SELECT 1 FROM {db.SCHEMA}.ingest_external_api WHERE ingest_id = %s",
            (ingest_id,),
        ).fetchone()
    if not has_api:
        click.echo(f"Warning: thing '{name}' has no external API, the job will fail.")
    _add("resync_thing", schedule, jitter, params, note, ingest_id)


@add.command("sync-sms")
@click.argument("origin")
@_common
def add_sync_sms(origin, schedule, jitter, note):
    _add("sync_sms", schedule, jitter, _params("sync_sms", origin=origin), note)


@add.command("mqtt-monitoring")
@_common
def add_mqtt_monitoring(schedule, jitter, note):
    _add("mqtt_monitoring", schedule, jitter, _params("mqtt_monitoring"), note)


def _update(table: str, key: str, key_value, column: str, value) -> int:
    with _connect() as conn:
        cur = conn.execute(
            f"UPDATE {db.SCHEMA}.{table} SET {column} = %s, updated_at = now() "
            f"WHERE {key} = %s",
            (value, key_value),
        )
        return cur.rowcount


def _update_job(job_id: int, column: str, value) -> None:
    if _update("scheduled_job", "id", job_id, column, value) == 0:
        raise click.ClickException(f"No job with id {job_id}")


@cli.command()
@click.argument("job_id", type=int)
def enable(job_id):
    """Enable a job."""
    _update_job(job_id, "enabled", True)


@cli.command()
@click.argument("job_id", type=int)
def disable(job_id):
    """Disable a job (defaults come back when removed, so disable them)."""
    _update_job(job_id, "enabled", False)


@cli.command("set-schedule")
@click.argument("job_id", type=int)
@click.argument("expression")
def set_schedule(job_id, expression):
    """Change the cron expression of a job."""
    _update_job(job_id, "cron_expression", _expression(expression, True))


@cli.command()
@click.argument("job_id", type=int)
def rm(job_id):
    """Delete a job."""
    with _connect() as conn:
        cur = conn.execute(
            f"DELETE FROM {db.SCHEMA}.scheduled_job WHERE id = %s", (job_id,)
        )
        if cur.rowcount == 0:
            raise click.ClickException(f"No job with id {job_id}")


# ---- thing schedules (written by the DSM API) ----


def _interval_of(expression: str) -> int | None:
    try:
        return schedule.get_current_interval(expression)
    except Exception:
        return None


def _mismatch(expression: str, configured: int | None) -> bool:
    if configured is None:
        return False
    return _interval_of(expression) != schedule.adjust_interval(configured)


def _configured_interval(conn: psycopg.Connection, ingest_id: int) -> int | None:
    row = conn.execute(
        f"""
        SELECT COALESCE(s.sync_interval_in_minutes, a.sync_interval_in_minutes)
        FROM {db.SCHEMA}.ingest i
        LEFT JOIN {db.SCHEMA}.ingest_external_sftp s ON s.ingest_id = i.id
        LEFT JOIN {db.SCHEMA}.ingest_external_api a ON a.ingest_id = i.id
        WHERE i.id = %s
        """,
        (ingest_id,),
    ).fetchone()
    return row[0] if row else None


@cli.group()
def thing():
    """Inspect and hand-tune thing sync schedules; `enabled` follows the DSM."""


@thing.command("list")
def thing_list():
    """List thing schedules; '!' marks a cron interval differing from the DSM's."""
    with _connect() as conn:
        rows = conn.execute(f"""
            SELECT i.uuid::text, i.name, sch.cron_expression, sch.jitter_seconds,
                   sch.enabled, sch.sync_interval_minutes,
                   COALESCE(s.sync_interval_in_minutes, a.sync_interval_in_minutes)
            FROM {db.SCHEMA}.ingest_schedule sch
            JOIN {db.SCHEMA}.ingest i ON i.id = sch.ingest_id
            LEFT JOIN {db.SCHEMA}.ingest_external_sftp s ON s.ingest_id = i.id
            LEFT JOIN {db.SCHEMA}.ingest_external_api a ON a.ingest_id = i.id
            ORDER BY i.id
            """).fetchall()
    click.echo("uuid  name  schedule  jitter  enabled  stored/configured/cron [min]")
    for uuid, name, expression, jitter, enabled, stored, configured in rows:
        flag = " !" if _mismatch(expression, configured) else ""
        click.echo(
            f"{uuid}  {name}  {expression}  {jitter}s  {'yes' if enabled else 'no'}  "
            f"{stored}/{configured}/{_interval_of(expression)}{flag}"
        )


def _update_thing(thing_uuid: str, column: str, value, expression=None) -> None:
    with _connect() as conn:
        ingest_id, name = _lookup(conn, thing_uuid)
        configured = _configured_interval(conn, ingest_id)
    if expression and _mismatch(expression, configured):
        click.echo(
            f"Warning: '{name}' is configured for {configured} min, "
            f"the expression runs every {_interval_of(expression)} min."
        )
    if _update("ingest_schedule", "ingest_id", ingest_id, column, value) == 0:
        raise click.ClickException(
            f"'{name}' has no schedule; set a sync interval in the DSM first"
        )


@thing.command("set-schedule")
@click.argument("thing_uuid")
@click.argument("expression")
def thing_set_schedule(thing_uuid, expression):
    """Hand-tune the 5-field cron expression; kept until the interval changes."""
    expression = _expression(expression, allow_seconds=False)
    _update_thing(thing_uuid, "cron_expression", expression, expression)


@thing.command("set-jitter")
@click.argument("thing_uuid")
@click.argument("seconds", type=click.IntRange(0, schedule.MAX_JITTER_SECONDS))
def thing_set_jitter(thing_uuid, seconds):
    """Set the start delay in seconds."""
    _update_thing(thing_uuid, "jitter_seconds", seconds)


if __name__ == "__main__":
    cli()
