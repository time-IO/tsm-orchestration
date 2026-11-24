#!/usr/bin/env python3
"""Render the crontab from the DSM DB and supervise supercronic."""

from __future__ import annotations

import hashlib
import logging
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

import click
import psycopg

from timeio.cron import db, jobs, legacy
from timeio.common import get_envvar, setup_logging

logger = logging.getLogger("cron-scheduler")

DEFAULT_CRON_DIR = "/tmp/crontab"
DEFAULT_LEGACY_CRONTAB = "/tmp/cron/crontab.txt"
IMPORT_ERROR_AFTER = 5


def render_from_db(dsn: str, on_skip=None) -> str:
    """Render the crontab from the DB without importing or seeding."""
    with db.connect(dsn) as conn, conn.transaction():
        schedules = db.fetch_schedules(conn)
        job_rows = db.fetch_jobs(conn)
    return jobs.render_crontab(schedules, job_rows, on_skip)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class Scheduler:
    def __init__(self, dsn: str, crontab_dir: str, legacy_path: str, poll: int):
        self.dsn = dsn
        self.dir = Path(crontab_dir)
        self.path = self.dir / "crontab.txt"
        self.heartbeat = self.dir / ".heartbeat"
        self.legacy = Path(legacy_path)
        self.poll = poll
        self.proc: subprocess.Popen | None = None
        self.last_hash: str | None = None
        self.import_failures = 0
        self._last_skips: frozenset[str] = frozenset()

    def _import(self, conn: psycopg.Connection) -> bool:
        """Back up and import the legacy crontab. False keeps the legacy file."""
        try:
            legacy.backup_legacy(self.legacy)
            summary = legacy.import_legacy(conn, self.legacy.read_text())
        except Exception as e:
            self.import_failures += 1
            log = (
                logger.error
                if self.import_failures >= IMPORT_ERROR_AFTER
                else logger.warning
            )
            log(
                f"legacy crontab import failed ({self.import_failures}x), "
                f"keeping the legacy crontab: {e}"
            )
            return False
        logger.info(f"imported legacy crontab {self.legacy}: {summary}")
        return True

    def _render(self, schedules, job_rows) -> str:
        skips: list[str] = []
        text = jobs.render_crontab(schedules, job_rows, skips.append)
        if frozenset(skips) != self._last_skips:
            self._last_skips = frozenset(skips)
            for msg in skips:
                logger.warning(f"skipping invalid entry: {msg}")
        return text

    def compute(self) -> str:
        """Return the crontab supercronic should run; legacy while the import is pending."""
        with db.connect(self.dsn) as conn:
            if not db.is_imported(conn) and self.legacy.is_file():
                if not self._import(conn):
                    return self.legacy.read_text()
            if seeded := db.seed_defaults(conn):
                logger.info(f"seeded default jobs: {', '.join(seeded)}")
            with conn.transaction():
                schedules = db.fetch_schedules(conn)
                job_rows = db.fetch_jobs(conn)
        return self._render(schedules, job_rows)

    def install(self, text: str) -> bool:
        """Replace the crontab and reload supercronic if `text` changed and is valid."""
        digest = _digest(text)
        if digest == self.last_hash:
            return False
        tmp = self.dir / f"crontab.txt.{os.getpid()}.tmp"
        tmp.write_text(text)
        test = subprocess.run(
            ["supercronic", "-test", str(tmp)], capture_output=True, text=True
        )
        if test.returncode != 0:
            tmp.unlink(missing_ok=True)
            logger.error(
                f"rendered crontab is invalid, keeping the old one: {test.stderr[-500:]}"
            )
            return False
        os.replace(tmp, self.path)
        self.last_hash = digest
        if self.proc is not None:
            self.proc.send_signal(signal.SIGUSR2)
            logger.info("crontab changed, reloaded supercronic")
        return True

    def update(self) -> bool:
        """One poll. Returns True if the crontab was replaced."""
        try:
            text = self.compute()
        except psycopg.Error as e:
            logger.warning(f"cannot read schedules, keeping the current crontab: {e}")
            return False
        return self.install(text)

    def start(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        if self.path.is_file():
            self.last_hash = _digest(self.path.read_text())
        try:
            self.update()
        except Exception:
            logger.exception("initial crontab update failed")
        if not self.path.is_file():
            # DB unreachable on a fresh start: the legacy file beats running nothing
            if self.legacy.is_file():
                logger.warning(f"starting with the legacy crontab {self.legacy}")
                text = self.legacy.read_text()
            else:
                text = jobs.render_crontab([], [])
            self.path.write_text(text)
            self.last_hash = _digest(text)
        self.heartbeat.touch()
        self.proc = subprocess.Popen(["supercronic", "-split-logs", str(self.path)])

    def run(self) -> int:
        stop = threading.Event()

        def on_term(signum, frame):
            stop.set()
            if self.proc is not None:
                self.proc.send_signal(signal.SIGTERM)

        signal.signal(signal.SIGTERM, on_term)
        signal.signal(signal.SIGINT, on_term)
        self.start()
        while not stop.wait(self.poll):
            if self.proc.poll() is not None:
                return self.proc.returncode
            try:
                self.update()
            except Exception:
                logger.exception("crontab update failed")
            self.heartbeat.touch()
        return self.proc.wait()


@click.command()
@click.option(
    "--render-only",
    is_flag=True,
    help="Print the crontab rendered from the DB and exit (no import, no seeding).",
)
def main(render_only: bool):
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    dsn = get_envvar("DSMDB_DSN")
    if render_only:
        click.echo(render_from_db(dsn), nl=False)
        return
    scheduler = Scheduler(
        dsn,
        os.environ.get("CRON_DIR", DEFAULT_CRON_DIR),
        os.environ.get("CRON_LEGACY_CRONTAB", DEFAULT_LEGACY_CRONTAB),
        int(os.environ.get("CRON_SCHEDULER_POLL_INTERVAL_SECONDS", "60")),
    )
    sys.exit(scheduler.run())


if __name__ == "__main__":
    main()
