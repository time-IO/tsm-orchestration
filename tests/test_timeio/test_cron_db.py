import hashlib
import signal
import subprocess
from unittest.mock import MagicMock

import click.testing
import psycopg
import pytest
from crontab import CronTab

import cron_jobs
import cron_scheduler
import setup_crontab
from timeio import cron

U1 = "00000000-0000-0000-0000-000000000001"
U2 = "00000000-0000-0000-0000-000000000002"
CMD = "python3 /scripts/mqtt_sync_wrapper.py"
SUFFIX = "> $STDOUT 2> $STDERR"


class FakeResult:
    def __init__(self, rows):
        self.rows = rows
        self.rowcount = len(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def __iter__(self):
        return iter(self.rows)


class FakeConn:
    """Records statements; `results` maps an SQL substring to its rows."""

    def __init__(self, results=None, raises=None):
        self.results = results or {}
        self.raises = raises
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))
        if self.raises and self.raises[0] in sql:
            raise self.raises[1]
        for key, rows in self.results.items():
            if key in sql:
                return FakeResult(rows)
        return FakeResult([])

    def sql(self, needle):
        return [c for c in self.calls if needle in c[0]]


# ---- handler ----


class ProjectMock:
    name = "proj"


def thing_mock(uuid=U1, ext_api=None, ext_sftp=None):
    t = MagicMock()
    t.uuid, t.id, t.name, t.project = uuid, 11, "thing", ProjectMock()
    t.ext_api, t.ext_sftp = ext_api, ext_sftp
    return t


@pytest.fixture
def handler(tmp_path, monkeypatch):
    h = setup_crontab.CreateThingInCrontabHandler.__new__(
        setup_crontab.CreateThingInCrontabHandler
    )
    h.tabfile = str(tmp_path / "crontab.txt")
    h.dsmdb_dsn = "dsn"
    (tmp_path / "crontab.txt").write_text("")
    monkeypatch.setattr(setup_crontab, "journal", MagicMock())
    return h


def run_act(handler, monkeypatch, thing):
    monkeypatch.setattr(setup_crontab.Thing, "from_uuid", lambda *a, **k: thing)
    handler.act({"thing": thing.uuid}, MagicMock())


def api(interval=10, enabled=True):
    return MagicMock(sync_interval=interval, enabled=enabled, api_type_name="X")


def test_act_creates_and_updates_keeping_jitter(handler, monkeypatch):
    thing = thing_mock(ext_api=api(10))
    run_act(handler, monkeypatch, thing)
    job = next(iter(CronTab(tabfile=handler.tabfile)))
    jitter = cron.jitter_from_command(job.command)
    assert job.is_enabled()

    thing.ext_api = api(10, enabled=False)
    run_act(handler, monkeypatch, thing)
    jobs = list(CronTab(tabfile=handler.tabfile))
    assert len(jobs) == 1 and not jobs[0].is_enabled()
    assert cron.jitter_from_command(jobs[0].command) == jitter


def test_act_without_ext_creates_nothing_and_removes_existing(handler, monkeypatch):
    thing = thing_mock()
    run_act(handler, monkeypatch, thing)
    assert not list(CronTab(tabfile=handler.tabfile))

    thing.ext_api = api()
    run_act(handler, monkeypatch, thing)
    thing.ext_api = None
    run_act(handler, monkeypatch, thing)
    assert not list(CronTab(tabfile=handler.tabfile))


# ---- cron_jobs CLI ----


def invoke(monkeypatch, conn, *args):
    monkeypatch.setattr(cron_jobs, "_connect", lambda: conn)
    return click.testing.CliRunner().invoke(cron_jobs.cli, list(args))


def test_cli_add_resync_thing(monkeypatch):
    conn = FakeConn({"FROM dsm_db.ingest ": [(11, "thing")], "ingest_external_api": [(1,)], "RETURNING id": [(5,)]})  # fmt: skip
    r = invoke(monkeypatch, conn, "add", "resync-thing", U1, "--days", "14",
               "--schedule", "0 3 * * 0", "--jitter", "4")  # fmt: skip
    assert r.exit_code == 0, r.output
    args = conn.sql("INSERT INTO dsm_db.scheduled_job")[0][1]
    assert (
        args[0] == "resync_thing"
        and args[1] == 11
        and args[3:6] == ("0 3 * * 0", 4, True)
    )


@pytest.mark.parametrize(
    "args",
    [
        ("add", "sync-sms", "evil", "--schedule", "0 * * * *"),
        ("add", "sync-sms", "sms_cv", "--schedule", "bad"),
        ("add", "resync-thing", U1, "--days", "0", "--schedule", "0 * * * *"),
        ("add", "sync-sms", "sms_cv", "--schedule", "0 * * * *", "--jitter", "60"),
    ],
)
def test_cli_validation(monkeypatch, args):
    conn = FakeConn()
    r = invoke(monkeypatch, conn, *args)
    assert r.exit_code != 0 and not conn.sql("INSERT")


def test_cli_unknown_thing_and_job(monkeypatch):
    r = invoke(
        monkeypatch, FakeConn(), "add", "resync-thing", U1, "--schedule", "0 * * * *"
    )
    assert r.exit_code != 0 and "No ingest" in r.output
    assert invoke(monkeypatch, FakeConn(), "rm", "3").exit_code != 0


# ---- scheduler ----


@pytest.fixture
def scheduler(tmp_path, monkeypatch):
    s = cron_scheduler.Scheduler("dsn", str(tmp_path), 60, None)
    s.dir.mkdir(exist_ok=True)
    s.text = "# x\n"
    monkeypatch.setattr(s, "render", lambda: s.text)
    s.proc = MagicMock()
    s.run_calls = []

    def fake_run(cmd, **kw):
        s.run_calls.append(cmd)
        return subprocess.CompletedProcess(cmd, s.test_rc, "", "bad")

    s.test_rc = 0
    monkeypatch.setattr(cron_scheduler.subprocess, "run", fake_run)
    return s


def test_scheduler_replaces_and_reloads_on_change(scheduler):
    assert scheduler.update()
    assert scheduler.path.read_text() == "# x\n"
    scheduler.proc.send_signal.assert_called_once_with(signal.SIGUSR2)
    assert not scheduler.update()
    assert scheduler.proc.send_signal.call_count == 1
    scheduler.text = "# y\n"
    assert scheduler.update() and scheduler.proc.send_signal.call_count == 2


def test_scheduler_keeps_file_on_invalid_test(scheduler):
    scheduler.path.write_text("old\n")
    scheduler.test_rc = 1
    assert not scheduler.update()
    assert scheduler.path.read_text() == "old\n"
    assert not list(scheduler.dir.glob("*.tmp"))
    scheduler.proc.send_signal.assert_not_called()


def test_scheduler_keeps_file_on_db_error(scheduler, monkeypatch):
    scheduler.path.write_text("old\n")

    def boom():
        raise psycopg.OperationalError("down")

    monkeypatch.setattr(scheduler, "render", boom)
    assert not scheduler.update()
    assert scheduler.path.read_text() == "old\n" and not scheduler.run_calls


def test_scheduler_start_adopts_existing_file(scheduler, monkeypatch):
    scheduler.path.write_text("# x\n")
    popen = MagicMock()
    monkeypatch.setattr(cron_scheduler.subprocess, "Popen", popen)
    scheduler.start()
    assert scheduler.last_hash == hashlib.sha256(b"# x\n").hexdigest()
    assert not scheduler.run_calls and scheduler.heartbeat.exists()
    popen.assert_called_once()


def test_scheduler_start_survives_update_error(scheduler, monkeypatch):
    def boom():
        raise FileNotFoundError("supercronic")

    monkeypatch.setattr(scheduler, "update", boom)
    monkeypatch.setattr(cron_scheduler.subprocess, "Popen", MagicMock())
    scheduler.start()
    assert scheduler.path.exists() and scheduler.heartbeat.exists()
