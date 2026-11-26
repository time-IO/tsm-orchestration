import hashlib
import signal
import subprocess
from contextlib import nullcontext
from datetime import datetime, timezone
from unittest.mock import MagicMock

import psycopg
import pytest

import cron_scheduler
from timeio.cron import db, legacy
from timeio.cron.jobs import ScheduleRow

U1 = "00000000-0000-0000-0000-000000000001"
LEGACY = "5 * * * * python3 /scripts/mqtt_sync_wrapper.py sync-thing x\n"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


# ---- scheduler ----


class FakeDB:
    """Stands in for the DSM DB behind the timeio.cron.db functions."""

    def __init__(self):
        self.imported = False
        self.tables_id = "1"
        self.schedules = []
        self.down = None
        self.import_error = None
        self.seeded = []

    def conn(self):
        if self.down:
            raise self.down
        conn = MagicMock()
        conn.__enter__.return_value = conn
        conn.transaction.return_value = nullcontext()
        return conn


@pytest.fixture
def fake_db(monkeypatch):
    fake = FakeDB()

    def import_legacy(conn, text):
        if fake.import_error:
            raise fake.import_error
        fake.imported = True
        return legacy.ImportSummary(imported=1)

    def seed(conn):
        fake.seeded.append(fake.imported)
        return []

    monkeypatch.setattr(db, "connect", lambda dsn: fake.conn())
    monkeypatch.setattr(db, "tables_id", lambda conn: fake.tables_id)
    monkeypatch.setattr(db, "seed_defaults", seed)
    monkeypatch.setattr(db, "fetch_schedules", lambda conn: list(fake.schedules))
    monkeypatch.setattr(db, "fetch_jobs", lambda conn: [])
    monkeypatch.setattr(legacy, "import_legacy", import_legacy)
    return fake


@pytest.fixture
def scheduler(tmp_path, monkeypatch, fake_db):
    (tmp_path / "cron").mkdir()
    s = cron_scheduler.Scheduler(
        "dsn", str(tmp_path / "crontab"), str(tmp_path / "cron" / "crontab.txt"), 60
    )
    s.dir.mkdir()
    s.proc = MagicMock()
    s.test_rc = 0
    s.run_calls = []

    def fake_run(cmd, **kw):
        s.run_calls.append(cmd)
        return subprocess.CompletedProcess(cmd, s.test_rc, "", "bad")

    monkeypatch.setattr(cron_scheduler.subprocess, "run", fake_run)
    return s


def schedule(ingest_id=1, expression="5 * * * *"):
    return ScheduleRow(ingest_id, U1, "thing", "proj", expression, 0, True, T0)


def test_legacy_while_import_fails_then_switch(scheduler, fake_db):
    scheduler.legacy.write_text(LEGACY)
    fake_db.schedules = [schedule()]
    fake_db.import_error = psycopg.OperationalError("boom")

    assert scheduler.update()
    assert scheduler.path.read_text() == LEGACY
    assert scheduler.import_failures == 1 and fake_db.seeded == []
    assert (scheduler.legacy.parent / "crontab.txt.pre-db.bkp").read_text() == LEGACY

    fake_db.import_error = None
    assert scheduler.update()
    assert "sync-thing " + U1 in scheduler.path.read_text()
    assert fake_db.seeded == [True]
    assert scheduler.proc.send_signal.call_count == 2
    assert scheduler.legacy.read_text() == LEGACY


def test_backup_failure_blocks_import(scheduler, fake_db, monkeypatch):
    scheduler.legacy.write_text(LEGACY)

    def fail(path):
        raise PermissionError("read-only")

    monkeypatch.setattr(legacy, "backup_legacy", fail)
    scheduler.update()
    assert not fake_db.imported and scheduler.path.read_text() == LEGACY


def test_import_errors_escalate(scheduler, fake_db, caplog):
    scheduler.legacy.write_text(LEGACY)
    fake_db.import_error = RuntimeError("boom")
    for _ in range(cron_scheduler.IMPORT_ERROR_AFTER):
        scheduler.update()
    levels = [r.levelname for r in caplog.records if "import failed" in r.message]
    assert levels[-1] == "ERROR" and levels[0] == "WARNING"


def test_import_failure_marks_unhealthy_after_retries(scheduler, fake_db):
    scheduler.legacy.write_text(LEGACY)
    fake_db.import_error = RuntimeError("boom")
    for _ in range(cron_scheduler.IMPORT_ERROR_AFTER - 1):
        scheduler.update()
    assert not scheduler.import_failed.exists()
    scheduler.update()
    assert "boom" in scheduler.import_failed.read_text()

    fake_db.import_error = None
    scheduler.update()
    assert not scheduler.import_failed.exists()


def test_blocked_import_marks_unhealthy_at_once(scheduler, fake_db, caplog):
    scheduler.legacy.write_text(LEGACY)
    fake_db.import_error = legacy.ImportBlocked("line 3 cannot be imported")
    scheduler.update()
    assert "line 3" in scheduler.import_failed.read_text()
    assert scheduler.path.read_text() == LEGACY
    assert [r.levelname for r in caplog.records if "line 3" in r.message] == ["ERROR"]


def test_import_marker_removed_when_not_pending(scheduler, fake_db):
    scheduler.import_failed.write_text("old\n")
    scheduler.update()
    assert not scheduler.import_failed.exists()


def test_no_legacy_file_renders_from_db(scheduler, fake_db):
    fake_db.schedules = [schedule()]
    assert scheduler.update()
    assert "sync-thing " + U1 in scheduler.path.read_text()
    assert fake_db.seeded == [False] and not fake_db.imported


def test_imported_ignores_legacy_file(scheduler, fake_db):
    scheduler.legacy.write_text(LEGACY)
    legacy.mark_imported(scheduler.legacy, fake_db.tables_id)
    scheduler.update()
    assert LEGACY not in scheduler.path.read_text() and not fake_db.imported
    assert not (scheduler.legacy.parent / "crontab.txt.pre-db.bkp").exists()


def test_import_writes_marker_and_runs_once(scheduler, fake_db):
    scheduler.legacy.write_text(LEGACY)
    scheduler.update()
    assert legacy.is_imported(scheduler.legacy, fake_db.tables_id)
    fake_db.imported = False
    scheduler.update()
    assert not fake_db.imported


def test_recreated_tables_reimport(scheduler, fake_db):
    scheduler.legacy.write_text(LEGACY)
    scheduler.update()
    fake_db.imported, fake_db.tables_id = False, "2"
    scheduler.update()
    assert fake_db.imported and legacy.is_imported(scheduler.legacy, "2")


def test_marker_write_failure_keeps_legacy(scheduler, fake_db, monkeypatch):
    scheduler.legacy.write_text(LEGACY)

    def fail(path, tables_id):
        raise PermissionError("read-only")

    monkeypatch.setattr(legacy, "mark_imported", fail)
    scheduler.update()
    assert scheduler.path.read_text() == LEGACY and scheduler.import_failures == 1


def test_unchanged_hash_no_reload(scheduler, fake_db):
    fake_db.schedules = [schedule()]
    assert scheduler.update()
    assert not scheduler.update()
    assert len(scheduler.run_calls) == 1
    scheduler.proc.send_signal.assert_called_once_with(signal.SIGUSR2)
    fake_db.schedules = [schedule(expression="7 * * * *")]
    assert scheduler.update() and scheduler.proc.send_signal.call_count == 2


def test_invalid_test_keeps_file(scheduler):
    scheduler.path.write_text("old\n")
    scheduler.test_rc = 1
    assert not scheduler.update()
    assert scheduler.path.read_text() == "old\n"
    assert not list(scheduler.dir.glob("*.tmp"))
    scheduler.proc.send_signal.assert_not_called()


def test_db_error_keeps_file(scheduler, fake_db):
    scheduler.path.write_text("old\n")
    fake_db.down = psycopg.OperationalError("down")
    assert not scheduler.update()
    assert scheduler.path.read_text() == "old\n" and not scheduler.run_calls


def test_invalid_rows_warned_once(scheduler, fake_db, caplog):
    fake_db.schedules = [schedule(expression="bad")]
    scheduler.update()
    scheduler.update()
    assert len([r for r in caplog.records if "skipping" in r.message]) == 1


@pytest.fixture
def popen(monkeypatch):
    p = MagicMock()
    monkeypatch.setattr(cron_scheduler.subprocess, "Popen", p)
    return p


def test_start_adopts_existing_file(scheduler, fake_db, popen):
    fake_db.down = psycopg.OperationalError("down")
    scheduler.path.write_text("# x\n")
    scheduler.start()
    assert scheduler.last_hash == hashlib.sha256(b"# x\n").hexdigest()
    assert scheduler.path.read_text() == "# x\n" and scheduler.heartbeat.exists()
    popen.assert_called_once()


def test_start_db_down_uses_legacy(scheduler, fake_db, popen):
    scheduler.legacy.write_text(LEGACY)
    fake_db.down = psycopg.OperationalError("down")
    scheduler.start()
    assert scheduler.path.read_text() == LEGACY and scheduler.heartbeat.exists()


def test_start_db_down_without_legacy_is_empty(scheduler, fake_db, popen):
    fake_db.down = psycopg.OperationalError("down")
    scheduler.start()
    assert scheduler.path.exists() and "sync-thing" not in scheduler.path.read_text()


def test_start_survives_unexpected_error(scheduler, monkeypatch, popen):
    def boom():
        raise FileNotFoundError("supercronic")

    monkeypatch.setattr(scheduler, "update", boom)
    scheduler.start()
    assert scheduler.path.exists() and scheduler.heartbeat.exists()


def test_run_touches_heartbeat_and_exits_with_supercronic(
    scheduler, fake_db, popen, monkeypatch
):
    monkeypatch.setattr(cron_scheduler.signal, "signal", MagicMock())
    fake_db.down = psycopg.OperationalError("down")
    popen.return_value.poll.side_effect = [None, 3]
    popen.return_value.returncode = 3
    scheduler.poll = 0
    scheduler.heartbeat.touch()
    assert scheduler.run() == 3
    assert scheduler.heartbeat.exists()
