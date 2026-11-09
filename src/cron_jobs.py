#!/usr/bin/env python3
"""Maintain the custom cron jobs (`dsm_db.custom_job`) of the cron-scheduler."""

from __future__ import annotations

from random import randint

import click
import psycopg

from timeio import cron
from timeio.common import get_envvar


def _connect() -> psycopg.Connection:
    return psycopg.connect(get_envvar("DSMDB_DSN"))


def _lookup(conn: psycopg.Connection, table: str, uuid: str) -> tuple[int, str]:
    row = conn.execute(
        f"SELECT id, name FROM {cron.SCHEMA}.{table} WHERE uuid::text = %s", (uuid,)
    ).fetchone()
    if row is None:
        raise click.ClickException(f"No {table} found with uuid {uuid}")
    return row[0], row[1]


def _schedule(expression: str) -> str:
    if not cron.validate_expression(expression):
        raise click.BadParameter(f"invalid cron expression {expression!r}")
    return " ".join(expression.split())


def _jitter(jitter: int | None) -> int:
    return randint(0, cron.SYNC_JITTER_SECONDS) if jitter is None else jitter


def _params(job_type: str, **params) -> dict:
    try:
        return cron.validate_params(job_type, params)
    except ValueError as e:
        raise click.BadParameter(str(e))


def _common(f):
    f = click.option("--note", help="Who/why, shown in the crontab comment.")(f)
    f = click.option(
        "--jitter",
        type=click.IntRange(0, cron.MAX_JITTER_SECONDS),
        help="Start delay in seconds, random if omitted.",
    )(f)
    f = click.option("--schedule", required=True, help="5-field cron expression.")(f)
    return f


@click.group()
def cli():
    pass


@cli.command("list")
def list_jobs():
    with _connect() as conn:
        jobs = cron.fetch_jobs(conn)
    click.echo("id  type            target  schedule  enabled  note")
    for j in jobs:
        target = j.target_name or j.params.get("origin") or "-"
        click.echo(
            f"{j.id}  {j.job_type}  {target}  {j.cron_expression}  "
            f"{'yes' if j.enabled else 'no'}  {j.note or ''}"
        )


@cli.group()
def add():
    """Add a job."""


@add.command("resync-thing")
@click.argument("thing_uuid")
@click.option("--days", default=cron.DEFAULT_RESYNC_DAYS, show_default=True)
@_common
def add_resync_thing(thing_uuid, days, schedule, jitter, note):
    params = _params("resync_thing", days=days)
    expression, jitter = _schedule(schedule), _jitter(jitter)
    with _connect() as conn:
        ingest_id, name = _lookup(conn, "ingest", thing_uuid)
        has_api = conn.execute(
            f"SELECT 1 FROM {cron.SCHEMA}.ingest_external_api WHERE ingest_id = %s",
            (ingest_id,),
        ).fetchone()
        if not has_api:
            click.echo(f"Warning: thing '{name}' has no ext_api, the job will fail.")
        job_id = cron.insert_job(
            conn, "resync_thing", expression, jitter, params,
            ingest_id=ingest_id, note=note,
        )  # fmt: skip
    click.echo(f"Added job {job_id}")


@add.command("resync-project")
@click.argument("project_uuid")
@click.option("--days", default=cron.DEFAULT_RESYNC_DAYS, show_default=True)
@_common
def add_resync_project(project_uuid, days, schedule, jitter, note):
    params = _params("resync_project", days=days)
    expression, jitter = _schedule(schedule), _jitter(jitter)
    with _connect() as conn:
        pg_id, _ = _lookup(conn, "permission_group", project_uuid)
        job_id = cron.insert_job(
            conn, "resync_project", expression, jitter, params,
            permission_group_id=pg_id, note=note,
        )  # fmt: skip
    click.echo(f"Added job {job_id}")


@add.command("sync-sms")
@click.argument("origin")
@_common
def add_sync_sms(origin, schedule, jitter, note):
    params = _params("sync_sms", origin=origin)
    expression, jitter = _schedule(schedule), _jitter(jitter)
    with _connect() as conn:
        job_id = cron.insert_job(
            conn, "sync_sms", expression, jitter, params, note=note
        )
    click.echo(f"Added job {job_id}")


def _update(job_id: int, column: str, value) -> None:
    with _connect() as conn:
        cur = conn.execute(
            f"UPDATE {cron.SCHEMA}.custom_job SET {column} = %s, updated_at = now() "
            "WHERE id = %s",
            (value, job_id),
        )
        if cur.rowcount == 0:
            raise click.ClickException(f"No job with id {job_id}")


@cli.command()
@click.argument("job_id", type=int)
def enable(job_id):
    _update(job_id, "enabled", True)


@cli.command()
@click.argument("job_id", type=int)
def disable(job_id):
    _update(job_id, "enabled", False)


@cli.command("set-schedule")
@click.argument("job_id", type=int)
@click.argument("expression")
def set_schedule(job_id, expression):
    _update(job_id, "cron_expression", _schedule(expression))


@cli.command()
@click.argument("job_id", type=int)
def rm(job_id):
    with _connect() as conn:
        cur = conn.execute(
            f"DELETE FROM {cron.SCHEMA}.custom_job WHERE id = %s", (job_id,)
        )
        if cur.rowcount == 0:
            raise click.ClickException(f"No job with id {job_id}")


if __name__ == "__main__":
    cli()
