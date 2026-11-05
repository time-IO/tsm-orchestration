import hashlib
import signal
import threading
import subprocess
from unittest.mock import MagicMock

import click.testing
import psycopg
import pytest
from crontab import CronTab

import cron_jobs
import cron_scheduler
import mqtt_sync_wrapper
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


def patch_connect(monkeypatch, module, conn):
    monkeypatch.setattr(module.psycopg, "connect", lambda *a, **k: conn)


# ---- backfill ----

LEGACY = (
    f"5-59/10 * * * * sleep 3 && {CMD} sync-thing {U1} {SUFFIX}\n"
    f"5-59/20 * * * * {CMD} sync-thing {U1} {SUFFIX}\n"
    f"# 1-59/10 * * * * {CMD} sync-thing {U2} {SUFFIX}\n"
    f"0 3 * * 0 {CMD} resync-range {U1} --days 14 {SUFFIX}\n"
    f"0 3 * * 1 {CMD} resync-range {U2} {SUFFIX}\n"
    f"10 * * * * {CMD} sync-sms sms_cv {SUFFIX}\n"
    "0 0 * * * /unknown.sh\n"
)


def test_backfill_imports(tmp_path, monkeypatch):
    f = tmp_path / "crontab.txt"
    f.write_text(LEGACY)
    conn = FakeConn(
        {"FROM dsm_db.ingest": [(U1, 11)], "count(*)": [(0,)], "RETURNING id": [(1,)]}
    )
    patch_connect(monkeypatch, cron, conn)
    s = cron.backfill_from_file(f, "dsn")
    upserts = conn.sql("INSERT INTO dsm_db.ingest_schedule")
    assert [c[1] for c in upserts] == [(11, "5-59/10 * * * *", 3, True)]
    jobs = conn.sql("INSERT INTO dsm_db.scheduled_job")
    assert [c[1][0] for c in jobs] == ["resync_thing", "sync_sms"]
    assert (s.imported, s.skipped, s.orphaned, s.unknown) == (3, 1, 2, 1)


def test_backfill_keeps_existing_jobs(tmp_path, monkeypatch):
    f = tmp_path / "crontab.txt"
    f.write_text(LEGACY)
    conn = FakeConn({"FROM dsm_db.ingest": [(U1, 11)], "count(*)": [(4,)]})
    patch_connect(monkeypatch, cron, conn)
    cron.backfill_from_file(f, "dsn")
    assert not conn.sql("INSERT INTO dsm_db.scheduled_job")
    assert len(conn.sql("INSERT INTO dsm_db.ingest_schedule")) == 1


def test_backfill_missing_table_or_file(tmp_path, monkeypatch):
    assert cron.backfill_from_file(tmp_path / "nope", "dsn") is None
    f = tmp_path / "crontab.txt"
    f.write_text(LEGACY)
    conn = FakeConn(raises=("FROM dsm_db.ingest", psycopg.errors.UndefinedTable()))
    patch_connect(monkeypatch, cron, conn)
    assert cron.backfill_from_file(f, "dsn") is None


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
    h._backfilled = True
    h._lock = threading.Lock()
    (tmp_path / "crontab.txt").write_text("")
    monkeypatch.setattr(setup_crontab, "journal", MagicMock())
    conn = FakeConn()
    patch_connect(monkeypatch, setup_crontab, conn)
    h.conn = conn
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
    expr, jitter = str(job.slices), cron.jitter_from_command(job.command)
    assert handler.conn.sql("INSERT INTO dsm_db.ingest_schedule")[-1][1] == (
        11, expr, jitter, True,
    )  # fmt: skip

    thing.ext_api = api(10, enabled=False)
    run_act(handler, monkeypatch, thing)
    jobs = list(CronTab(tabfile=handler.tabfile))
    assert len(jobs) == 1 and not jobs[0].is_enabled()
    assert cron.jitter_from_command(jobs[0].command) == jitter
    assert handler.conn.sql("INSERT INTO dsm_db.ingest_schedule")[-1][1] == (
        11, expr, jitter, False,
    )  # fmt: skip


def test_act_without_ext_creates_nothing_and_removes_existing(handler, monkeypatch):
    thing = thing_mock()
    run_act(handler, monkeypatch, thing)
    assert not list(CronTab(tabfile=handler.tabfile))
    assert not handler.conn.sql("INSERT INTO")

    thing.ext_api = api()
    run_act(handler, monkeypatch, thing)
    thing.ext_api = None
    run_act(handler, monkeypatch, thing)
    assert not list(CronTab(tabfile=handler.tabfile))
    assert handler.conn.sql("DELETE FROM dsm_db.ingest_schedule")[-1][1] == (11,)


def test_act_db_failure_keeps_file(handler, monkeypatch):
    handler.conn.raises = ("INSERT", psycopg.OperationalError("down"))
    run_act(handler, monkeypatch, thing_mock(ext_api=api()))
    assert len(list(CronTab(tabfile=handler.tabfile))) == 1


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
        and args[4:7] == ("0 3 * * 0", 4, True)
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


# ---- resync-project ----


def test_resync_project_only_ext_api(monkeypatch):
    things = [thing_mock(U1, ext_api=api()), thing_mock(U2, ext_sftp=MagicMock())]
    project = MagicMock()
    project.get_things.return_value = things
    monkeypatch.setattr(mqtt_sync_wrapper.Project, "from_uuid", lambda *a, **k: project)
    published = []
    monkeypatch.setattr(
        mqtt_sync_wrapper, "publish_multiple", lambda t, p: published.append((t, p))
    )
    monkeypatch.setenv("DSMDB_DSN", "dsn")
    monkeypatch.setenv("API_SYNC_TOPIC", "api/topic")
    r = click.testing.CliRunner().invoke(
        mqtt_sync_wrapper.cli, ["resync-project", "p", "--days", "2"]
    )
    assert r.exit_code == 0, r.output
    assert len(published) == 1 and published[0][0] == "api/topic"
    assert len(published[0][1]) == 1 and U1 in published[0][1][0]


def test_resync_project_without_ext_api_publishes_nothing(monkeypatch):
    project = MagicMock()
    project.get_things.return_value = [thing_mock(U2)]
    monkeypatch.setattr(mqtt_sync_wrapper.Project, "from_uuid", lambda *a, **k: project)
    monkeypatch.setattr(
        mqtt_sync_wrapper, "publish_multiple", MagicMock(side_effect=AssertionError)
    )
    monkeypatch.setenv("DSMDB_DSN", "dsn")
    r = click.testing.CliRunner().invoke(mqtt_sync_wrapper.cli, ["resync-project", "p"])
    assert r.exit_code == 0, r.output


def test_publish_multiple_uses_one_connection(monkeypatch):
    from timeio import mqtt

    for k, v in {
        "MQTT_BROKER": "h:1883", "MQTT_QOS": "1", "MQTT_USER": "u", "MQTT_PASSWORD": "p",
    }.items():  # fmt: skip
        monkeypatch.setenv(k, v)
    multiple = MagicMock()
    monkeypatch.setattr(mqtt.paho.mqtt.publish, "multiple", multiple)
    mqtt.publish_multiple("t", ["a", "b"])
    msgs = multiple.call_args.args[0]
    assert [m["payload"] for m in msgs] == ["a", "b"]
    assert all(m["topic"] == "t" and m["qos"] == 1 for m in msgs)
    assert multiple.call_args.kwargs["hostname"] == "h"


# ---- backfill retry ----


def test_ensure_backfill_retries_until_tables_exist(handler, monkeypatch):
    results = iter([None, None, cron.BackfillSummary()])
    monkeypatch.setattr(setup_crontab, "backfill_from_file", lambda *a: next(results))
    handler._backfilled = False
    for expected in (False, False, True):
        handler.ensure_backfill()
        assert handler._backfilled is expected
    handler.ensure_backfill()  # no further call once done


def test_ensure_backfill_survives_errors(handler, monkeypatch):
    def boom(*a):
        raise psycopg.OperationalError("down")

    monkeypatch.setattr(setup_crontab, "backfill_from_file", boom)
    handler._backfilled = False
    handler.ensure_backfill()
    assert handler._backfilled is False


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
