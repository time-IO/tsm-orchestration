from contextlib import contextmanager

import pytest

from timeio.cron import db, legacy

U1 = "00000000-0000-0000-0000-000000000001"
U2 = "00000000-0000-0000-0000-000000000002"
U3 = "00000000-0000-0000-0000-000000000003"
CMD = "python3 /scripts/mqtt_sync_wrapper.py"


class Result:
    def __init__(self, rows=(), rowcount=None):
        self.rows = list(rows)
        self.rowcount = len(self.rows) if rowcount is None else rowcount

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class FakeDB:
    """In-memory stand-in for the statements of timeio.cron.db/legacy."""

    def __init__(self, ingests=None, schedules=None, jobs=None, imported=False):
        self.ingests = ingests or {}  # uuid -> (ingest_id, interval)
        self.schedules = dict(schedules or {})  # ingest_id -> row tuple
        self.jobs = list(jobs or [])  # dicts
        self.imported = imported
        self.rolled_back = False

    @contextmanager
    def transaction(self):
        snapshot = (dict(self.schedules), list(self.jobs), self.imported)
        try:
            yield
        except Exception:
            self.schedules, self.jobs, self.imported = snapshot
            self.rolled_back = True
            raise

    def execute(self, sql, params=None):
        sql = " ".join(sql.split())
        if "FROM dsm_db.cron_legacy_import" in sql:
            return Result([(1,)] if self.imported else [])
        if "INSERT INTO dsm_db.cron_legacy_import" in sql:
            self.imported = True
            return Result()
        if "FROM dsm_db.ingest i" in sql:
            rows = [(u, *self.ingests[u]) for u in params[0] if u in self.ingests]
            return Result(rows)
        if "INSERT INTO dsm_db.ingest_schedule" in sql:
            if params[0] in self.schedules:
                return Result(rowcount=0)
            self.schedules[params[0]] = params[1:]
            return Result(rowcount=1)
        if "SELECT 1 FROM dsm_db.scheduled_job" in sql:
            job_type, params_, ingest_id, expr, _ = params
            hit = any(
                j["job_type"] == job_type
                and params_.obj.items() <= j["params"].items()
                and j["ingest_id"] == ingest_id
                and (expr is None or j["expr"] == expr)
                for j in self.jobs
            )
            return Result([(1,)] if hit else [])
        if "INSERT INTO dsm_db.scheduled_job" in sql:
            job_type, ingest_id, params_, expr, jitter, enabled, note = params
            self.jobs.append(
                dict(
                    job_type=job_type,
                    ingest_id=ingest_id,
                    params=params_.obj,
                    expr=expr,
                    jitter=jitter,
                    enabled=enabled,
                    note=note,
                )
            )
            return Result([(len(self.jobs),)])
        raise AssertionError(f"unexpected SQL: {sql}")


LEGACY = f"""\
*/30 * * * * * * /scripts/mqtt_sync_wrapper.py mqtt-monitoring > $STDOUT 2>$STDERR
5-59/10 * * * * sleep 12 && {CMD} sync-thing {U1} > $STDOUT 2> $STDERR
# 7 */2 * * * sleep 3 && {CMD} sync-thing {U2} > $STDOUT 2> $STDERR
0 4 * * MON /scripts/mqtt_sync_wrapper resync-range {U1} --days 8
0 4 * * MON /scripts/mqtt_sync_wrapper resync-range {U1} --days 8
5 * * * * {CMD} sync-thing {U3}
5-59 * * * * {CMD} sync-sms sms_backend
0 0 * * * /usr/bin/something-else
"""


def test_import_legacy():
    conn = FakeDB(ingests={U1: (1, 10), U2: (2, None)})
    summary = legacy.import_legacy(conn, LEGACY)
    assert str(summary) == "imported=5 skipped=1 orphaned=1 unknown=1"
    assert conn.schedules == {
        1: ("5-59/10 * * * *", 12, True, 10),
        2: ("7 */2 * * *", 3, False, None),
    }
    assert [(j["job_type"], j["ingest_id"], j["params"], j["expr"]) for j in conn.jobs] == [
        ("mqtt_monitoring", None, {}, "*/30 * * * * * *"),
        ("resync_thing", 1, {"days": 8}, "0 4 * * MON"),
        ("sync_sms", None, {"origin": "sms_backend"}, "5-59 * * * *"),
    ]  # fmt: skip
    assert conn.imported


def test_import_keeps_existing_rows():
    conn = FakeDB(
        ingests={U1: (1, 10)},
        schedules={1: ("3-59/10 * * * *", 4, True, 10)},
        jobs=[
            dict(job_type="sync_sms", ingest_id=None, params={"origin": "sms_backend"},
                 expr="5-59 * * * *", jitter=0, enabled=False, note=None),
        ],
    )  # fmt: skip
    text = (
        f"5-59/10 * * * * sleep 12 && {CMD} sync-thing {U1}\n"
        f"5-59 * * * * {CMD} sync-sms sms_backend\n"
    )
    summary = legacy.import_legacy(conn, text)
    assert (summary.imported, summary.skipped) == (0, 2)
    assert conn.schedules[1] == ("3-59/10 * * * *", 4, True, 10)
    assert len(conn.jobs) == 1 and conn.jobs[0]["enabled"] is False


def test_import_refuses_second_run():
    conn = FakeDB(ingests={U1: (1, 10)}, imported=True)
    with pytest.raises(RuntimeError):
        legacy.import_legacy(conn, f"5 * * * * {CMD} sync-thing {U1}\n")
    assert conn.schedules == {} and conn.rolled_back


def test_seed_defaults():
    conn = FakeDB(
        jobs=[
            dict(job_type="sync_sms", ingest_id=None, params={"origin": "sms_backend"},
                 expr="5-59 * * * *", jitter=0, enabled=False, note=None),
            dict(job_type="sync_sms", ingest_id=None, params={"origin": "sms_cv"},
                 expr="0 * * * *", jitter=0, enabled=True, note=None),
        ]
    )  # fmt: skip
    assert db.seed_defaults(conn) == ["mqtt_monitoring"]
    assert conn.jobs[-1]["expr"] == "*/30 * * * * * *"
    assert db.seed_defaults(conn) == []


def test_seed_defaults_empty():
    conn = FakeDB()
    assert db.seed_defaults(conn) == ["mqtt_monitoring", "sync_sms"]
    assert conn.jobs[1]["params"] == {"origin": "sms_backend"}


def test_backup_legacy_writes_once(tmp_path):
    src = tmp_path / "crontab.txt"
    src.write_text("original\n")
    backup = legacy.backup_legacy(src)
    assert backup.name == "crontab.txt.pre-db.bkp"
    src.write_text("changed\n")
    legacy.backup_legacy(src)
    assert backup.read_text() == "original\n"
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "crontab.txt",
        "crontab.txt.pre-db.bkp",
    ]


def test_backup_legacy_raises_on_failure(tmp_path):
    with pytest.raises(OSError):
        legacy.backup_legacy(tmp_path / "missing.txt")
