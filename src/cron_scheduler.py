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

from timeio.cron import db, jobs
from timeio.common import get_envvar, setup_logging

logger = logging.getLogger("cron-scheduler")


def render_from_db(dsn: str, on_skip=None) -> tuple[str, int]:
    """Return the rendered crontab and the number of ingest schedules."""
    with db.connect(dsn) as conn, conn.transaction():
        schedules = db.fetch_schedules(conn)
        job_rows = db.fetch_jobs(conn)
    return jobs.render_crontab(schedules, job_rows, on_skip), len(schedules)


class Scheduler:
    def __init__(self, dsn: str, crontab_dir: str, poll: int):
        self.dsn = dsn
        self.dir = Path(crontab_dir)
        self.path = self.dir / "crontab.txt"
        self.heartbeat = self.dir / ".heartbeat"
        self.poll = poll
        self.proc: subprocess.Popen | None = None
        self.last_hash: str | None = None
        self._last_skips: frozenset[str] = frozenset()
        self._warned_empty = False

    def render(self) -> str:
        skips: list[str] = []
        text, n = render_from_db(self.dsn, on_skip=skips.append)
        if frozenset(skips) != self._last_skips:
            self._last_skips = frozenset(skips)
            for msg in skips:
                logger.warning(f"skipping invalid entry: {msg}")
        if n == 0 and not self._warned_empty:
            self._warned_empty = True
            logger.warning(
                "ingest_schedule is empty; was the backfill release skipped?"
            )
        return text

    def update(self) -> bool:
        """Render once, replace the crontab and reload on change. Returns True
        if the file was replaced."""
        try:
            text = self.render()
        except psycopg.Error as e:
            logger.warning(f"cannot read schedules, keeping the last crontab: {e}")
            return False
        digest = hashlib.sha256(text.encode()).hexdigest()
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

    def start(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        if self.path.is_file():
            self.last_hash = hashlib.sha256(self.path.read_bytes()).hexdigest()
        try:
            updated = self.update()
        except Exception:
            logger.exception("initial crontab update failed")
            updated = False
        if not updated and not self.path.is_file():
            self.path.write_text(jobs.render_crontab([], []))
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
@click.option("--render-only", is_flag=True, help="Print the crontab and exit.")
def main(render_only: bool):
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    dsn = get_envvar("DSMDB_DSN")
    if render_only:
        text, _ = render_from_db(dsn)
        click.echo(text, nl=False)
        return
    poll = int(os.environ.get("CRON_SCHEDULER_POLL_INTERVAL_SECONDS", "60"))
    sys.exit(Scheduler(dsn, os.environ.get("CRON_DIR", "/tmp/crontab"), poll).run())


if __name__ == "__main__":
    main()
