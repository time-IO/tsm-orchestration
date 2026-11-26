import hashlib
import signal
import subprocess
from contextlib import nullcontext
from datetime import datetime, timezone
from unittest.mock import MagicMock

import click.testing
import psycopg
import pytest

import cron_jobs
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
    monkeypatch.setattr(db, "is_imported", lambda conn: fake.imported)
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
    fake_db.imported = True
    scheduler.update()
    assert LEGACY not in scheduler.path.read_text()
    assert not (scheduler.legacy.parent / "crontab.txt.pre-db.bkp").exists()


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


# ---- cron_jobs CLI ----


class Result:
    def __init__(self, rows):
        self.rows = rows
        self.rowcount = len(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class FakeConn:
    """Records statements; `results` maps an SQL substring to its rows."""

    def __init__(self, results=None):
        self.results = results or {}
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))
        for key, rows in self.results.items():
            if key in sql:
                return Result(rows)
        return Result([])

    def sql(self, needle):
        return [c for c in self.calls if needle in c[0]]


def invoke(monkeypatch, conn, *args):
    monkeypatch.setattr(cron_jobs, "_connect", lambda: conn)
    return click.testing.CliRunner().invoke(cron_jobs.cli, list(args))


def test_cli_add_resync_thing(monkeypatch):
    conn = FakeConn({"FROM dsm_db.ingest ": [(11, "thing")], "ingest_external_api": [(1,)], "RETURNING id": [(5,)]})  # fmt: skip
    r = invoke(monkeypatch, conn, "add", "resync-thing", U1, "--days", "14",
               "--schedule", "0 3 * * 0", "--jitter", "4")  # fmt: skip
    assert r.exit_code == 0, r.output
    assert "Warning" not in r.output and "Added job 5" in r.output
    args = conn.sql("INSERT INTO dsm_db.scheduled_job")[0][1]
    assert args[0:2] == ("resync_thing", 11) and args[2].obj == {"days": 14}
    assert args[3:6] == ("0 3 * * 0", 4, True)


def test_cli_add_resync_thing_warns_without_api(monkeypatch):
    conn = FakeConn({"FROM dsm_db.ingest ": [(11, "thing")], "RETURNING id": [(5,)]})
    r = invoke(monkeypatch, conn, "add", "resync-thing", U1, "--schedule", "0 3 * * 0")
    assert r.exit_code == 0 and "no external API" in r.output


def test_cli_add_mqtt_monitoring_with_seconds(monkeypatch):
    conn = FakeConn({"RETURNING id": [(7,)]})
    r = invoke(monkeypatch, conn, "add", "mqtt-monitoring",
               "--schedule", "*/30 * * * * * *", "--jitter", "0")  # fmt: skip
    assert r.exit_code == 0, r.output
    args = conn.sql("INSERT INTO dsm_db.scheduled_job")[0][1]
    assert args[0] == "mqtt_monitoring" and args[2].obj == {}
    assert args[3:5] == ("*/30 * * * * * *", 0)


@pytest.mark.parametrize(
    "args",
    [
        ("add", "sync-sms", "evil", "--schedule", "0 * * * *"),
        ("add", "sync-sms", "sms_cv", "--schedule", "bad"),
        ("add", "resync-thing", U1, "--days", "0", "--schedule", "0 * * * *"),
        ("add", "sync-sms", "sms_cv", "--schedule", "0 * * * *", "--jitter", "60"),
        ("set-schedule", "3", "nope"),
        ("thing", "set-schedule", U1, "*/30 * * * * * *"),
        ("thing", "set-jitter", U1, "60"),
    ],
)
def test_cli_validation(monkeypatch, args):
    conn = FakeConn()
    r = invoke(monkeypatch, conn, *args)
    assert r.exit_code != 0 and not conn.sql("INSERT") and not conn.sql("UPDATE")


def test_cli_unknown_thing_and_job(monkeypatch):
    r = invoke(
        monkeypatch, FakeConn(), "add", "resync-thing", U1, "--schedule", "0 * * * *"
    )
    assert r.exit_code != 0 and "No ingest" in r.output
    assert invoke(monkeypatch, FakeConn(), "rm", "3").exit_code != 0
    assert invoke(monkeypatch, FakeConn(), "disable", "3").exit_code != 0


def test_cli_job_set_schedule(monkeypatch):
    conn = FakeConn({"UPDATE": [(1,)]})
    r = invoke(monkeypatch, conn, "set-schedule", "3", "0  4 * * MON")
    assert r.exit_code == 0, r.output
    sql, params = conn.sql("UPDATE dsm_db.scheduled_job")[0]
    assert "cron_expression = %s" in sql and params == ("0 4 * * MON", 3)


def test_cli_thing_list(monkeypatch):
    rows = [
        (U1, "a", "17 */2 * * *", 5, True, 120, 120),
        ("u2", "b", "5,25 * * * *", 0, False, 30, 30),
        ("u3", "c", "3 * * * *", 0, False, None, None),
    ]
    r = invoke(monkeypatch, FakeConn({"FROM dsm_db.ingest_schedule": rows}), "thing", "list")  # fmt: skip
    lines = r.output.splitlines()[1:]
    assert r.exit_code == 0, r.output
    assert lines[0].endswith("120/120/120")
    assert lines[1].endswith("30/30/20 !") and " no " in lines[1]
    assert lines[2].endswith("None/None/60")


def thing_conn(configured=60, updated=1):
    return FakeConn({
        "FROM dsm_db.ingest WHERE": [(11, "thing")],
        "COALESCE": [(configured,)],
        "UPDATE": [(1,)] * updated,
    })  # fmt: skip


def test_cli_thing_set_schedule(monkeypatch):
    conn = thing_conn()
    r = invoke(monkeypatch, conn, "thing", "set-schedule", U1, "17 * * * *")
    assert r.exit_code == 0 and "Warning" not in r.output, r.output
    sql, params = conn.sql("UPDATE dsm_db.ingest_schedule")[0]
    assert "cron_expression = %s" in sql and params == ("17 * * * *", 11)


def test_cli_thing_set_schedule_warns_on_mismatch(monkeypatch):
    r = invoke(monkeypatch, thing_conn(), "thing", "set-schedule", U1, "*/10 * * * *")
    assert r.exit_code == 0 and "every 10 min" in r.output


def test_cli_thing_without_schedule(monkeypatch):
    r = invoke(monkeypatch, thing_conn(updated=0), "thing", "set-jitter", U1, "7")
    assert r.exit_code != 0 and "no schedule" in r.output


def test_cli_thing_set_jitter(monkeypatch):
    conn = thing_conn()
    r = invoke(monkeypatch, conn, "thing", "set-jitter", U1, "7")
    assert r.exit_code == 0, r.output
    assert conn.sql("UPDATE dsm_db.ingest_schedule")[0][1] == (7, 11)


def test_cli_add_trigger_qc(monkeypatch):
    conn = FakeConn({"FROM dsm_db.quality_control_setting": [(9,)], "RETURNING id": [(4,)]})  # fmt: skip
    r = invoke(monkeypatch, conn, "add", "trigger-qc", U1, "--interval", "1h",
               "--schedule", "0 * * * *", "--jitter", "2")  # fmt: skip
    assert r.exit_code == 0, r.output
    args = conn.sql("INSERT INTO dsm_db.scheduled_job")[0][1]
    assert (
        args[0] == "trigger_qc"
        and args[1] is None
        and args[2].obj == {"interval": "1h"}
    )
    assert args[3:5] == ("0 * * * *", 2) and args[7] == 9


@pytest.mark.parametrize(
    ("args", "message"),
    [(("--interval", "1 hour"), "interval"), (("--interval", "1h"), "No QC settings")],
)
def test_cli_add_trigger_qc_rejects(monkeypatch, args, message):
    conn = FakeConn()
    r = invoke(
        monkeypatch, conn, "add", "trigger-qc", U1, *args, "--schedule", "0 * * * *"
    )
    assert r.exit_code != 0 and message in r.output and not conn.sql("INSERT")
