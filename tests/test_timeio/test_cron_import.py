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

    def __init__(self, ingests=None, jobs=None, qc=None, configs=None, schedules=None):
        self.ingests = ingests or {}  # uuid -> ingest_id
        self.configs = configs or {}  # ingest_id -> (sync interval, sync enabled)
        # ingest_id -> [expression, jitter, enabled, interval]
        self.schedules = {k: list(v) for k, v in (schedules or {}).items()}
        self.qc = qc or {}  # (group uuid, lower name) -> qc setting id
        self.jobs = list(jobs or [])  # dicts
        self.rolled_back = False

    @contextmanager
    def transaction(self):
        snapshot = list(self.jobs), {k: list(v) for k, v in self.schedules.items()}
        try:
            yield
        except Exception:
            self.jobs, self.schedules = snapshot
            self.rolled_back = True
            raise

    def execute(self, sql, params=None):
        sql = " ".join(sql.split())
        if "FROM dsm_db.quality_control_setting q" in sql:
            qc_id = self.qc.get((params[0], params[1].lower()))
            return Result([(qc_id,)] if qc_id else [])
        if "LEFT JOIN dsm_db.ingest_external_sftp" in sql:
            ids = {u: self.ingests[u] for u in params[0] if u in self.ingests}
            return Result(
                [(u, i, *self.configs[i]) for u, i in ids.items() if i in self.configs]
            )
        if "INSERT INTO dsm_db.ingest_schedule" in sql:
            ingest_id, expr, jitter, enabled, interval = params
            row = self.schedules.get(ingest_id)
            if row is None:
                self.schedules[ingest_id] = [expr, jitter, enabled, interval]
            elif row[:2] == [expr, jitter]:
                return Result(rowcount=0)
            else:
                row[:2] = [expr, jitter]
            return Result(rowcount=1)
        if "FROM dsm_db.ingest i" in sql:
            rows = [(u, self.ingests[u]) for u in params[0] if u in self.ingests]
            return Result(rows)
        if "SELECT 1 FROM dsm_db.scheduled_job" in sql:
            job_type, params_, ingest_id, qc_id, expr, _ = params
            hit = any(
                j["job_type"] == job_type
                and params_.obj.items() <= j["params"].items()
                and j["ingest_id"] == ingest_id
                and j.get("qc_id") == qc_id
                and (expr is None or j["expr"] == expr)
                for j in self.jobs
            )
            return Result([(1,)] if hit else [])
        if "INSERT INTO dsm_db.scheduled_job" in sql:
            job_type, ingest_id, params_, expr, jitter, enabled, note, qc_id = params
            self.jobs.append(
                dict(
                    job_type=job_type,
                    ingest_id=ingest_id,
                    qc_id=qc_id,
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
# 0 0 * * * /usr/bin/something-else
"""


CONFIGS = {1: (10, True), 2: (None, True)}


def test_import_legacy():
    conn = FakeDB(ingests={U1: 1, U2: 2}, configs=CONFIGS)
    summary = legacy.import_legacy(conn, LEGACY)
    # U3 has no external ingest; minute and start delay come from the file,
    # interval and enabled from the DSM
    assert str(summary) == "imported=5 skipped=1 orphaned=1 unknown=1"
    assert conn.schedules == {
        1: ["5-59/10 * * * *", 12, True, 10],
        2: ["7 */2 * * *", 3, False, None],
    }
    assert [(j["job_type"], j["ingest_id"], j["params"], j["expr"]) for j in conn.jobs] == [
        ("mqtt_monitoring", None, {}, "*/30 * * * * * *"),
        ("resync_thing", 1, {"days": 8}, "0 4 * * MON"),
        ("sync_sms", None, {"origin": "sms_backend"}, "5-59 * * * *"),
    ]  # fmt: skip


def test_import_keeps_existing_rows():
    conn = FakeDB(
        ingests={U1: 1},
        configs={1: (10, True)},
        schedules={1: ["5-59/10 * * * *", 12, True, 10]},
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
    assert len(conn.jobs) == 1 and conn.jobs[0]["enabled"] is False


def test_import_twice_adds_nothing():
    conn = FakeDB(ingests={U1: 1, U2: 2}, configs=CONFIGS)
    legacy.import_legacy(conn, LEGACY)
    before = list(conn.jobs), {k: list(v) for k, v in conn.schedules.items()}
    summary = legacy.import_legacy(conn, LEGACY)
    assert summary.imported == 0 and (conn.jobs, conn.schedules) == before


def test_import_rolls_back_on_error():
    conn = FakeDB(ingests={U1: 1}, configs={1: (60, True)})
    text = f"5 * * * * {CMD} sync-thing {U1}\n0 0 * * * {CMD} sync-sms sms_backend\n"
    real = conn.execute

    def fail_on_jobs(sql, params=None):
        if "INSERT INTO dsm_db.scheduled_job" in sql:
            raise RuntimeError("boom")
        return real(sql, params)

    conn.execute = fail_on_jobs
    with pytest.raises(RuntimeError):
        legacy.import_legacy(conn, text)
    assert conn.jobs == [] and conn.rolled_back
    assert conn.schedules == {}


def test_imported_marker(tmp_path):
    src = tmp_path / "crontab.txt"
    src.write_text("x\n")
    assert not legacy.is_imported(src, "41")
    legacy.mark_imported(src, "41")
    assert legacy.is_imported(src, "41")
    # recreated tables (downgrade + upgrade) get a new id and re-import
    assert not legacy.is_imported(src, "42")
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "crontab.txt",
        "crontab.txt.imported",
    ]


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


G = "00000000-0000-0000-0000-0000000000aa"
QC = "python3 /scripts/trigger_qaqc.py"


def test_import_trigger_qc():
    conn = FakeDB(qc={(G, "my qc"): 7})
    text = (
        f"0 * * * * {QC} --interval 1h --project-uuid {G} --qc-settings-name 'My QC'\n"
        f"0 * * * * {QC} --interval 1h --project-uuid {G} --qc-settings-name 'my qc'\n"
        f"# 0 2 * * * {QC} --interval 1d --project-uuid {G} --qc-settings-name gone\n"
    )
    summary = legacy.import_legacy(conn, text)
    assert (summary.imported, summary.skipped, summary.orphaned) == (1, 1, 1)
    assert [
        (
            j["job_type"],
            j["qc_id"],
            j["ingest_id"],
            j["params"],
            j["expr"],
            j["enabled"],
        )
        for j in conn.jobs
    ] == [("trigger_qc", 7, None, {"interval": "1h"}, "0 * * * *", True)]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("0 0 * * * /usr/bin/something-else\n", "line 1 cannot be imported"),
        (f"@reboot {CMD} resync-range {U1}\n", "line 1 cannot be imported"),
        (f"5 * * * * {CMD} sync-thing {U1} --odd\n", "line 1 cannot be imported"),
    ],
)
def test_import_blocked(text, message):
    conn = FakeDB(ingests={U1: 1})
    with pytest.raises(legacy.ImportBlocked, match=message):
        legacy.import_legacy(conn, text)
    assert conn.jobs == []


def test_import_commented_unknown_is_dropped():
    conn = FakeDB()
    summary = legacy.import_legacy(conn, "# 0 0 * * * /usr/bin/x\n# a note\n")
    assert summary.unknown == 1


@pytest.mark.parametrize(
    ("line", "interval", "expected"),
    [
        # same interval: the line as is
        (f"12,42 * * * * sleep 4 && {CMD} sync-thing {U1}", 30, ["12,42 * * * *", 4]),
        (f"@hourly sleep 29 && {CMD} sync-thing {U1}", 60, ["0 * * * *", 29]),
        # the DSM interval differs: its step, the line's base minute
        (f"5 * * * * sleep 9 && {CMD} sync-thing {U1}", 30, ["5-59/30 * * * *", 9]),
        # a disabled line still sets minute and start delay
        (f"# 7 * * * * {CMD} sync-thing {U1}", 60, ["7 * * * *", 0]),
        # no DSM interval yet: keep the line for when one is set
        (f"7 * * * * sleep 2 && {CMD} sync-thing {U1}", None, ["7 * * * *", 2]),
    ],
)
def test_import_sync_thing(line, interval, expected):
    conn = FakeDB(ingests={U1: 1}, configs={1: (interval, True)})
    summary = legacy.import_legacy(conn, line + "\n")
    assert summary.imported == 1
    assert conn.schedules[1] == [*expected, interval is not None, interval]


def test_import_sync_thing_without_line_gets_no_row():
    conn = FakeDB(ingests={U1: 1, U2: 2}, configs={1: (60, True), 2: (60, True)})
    legacy.import_legacy(conn, f"5 * * * * {CMD} sync-thing {U1}\n")
    assert list(conn.schedules) == [1]


def test_import_sync_thing_after_dsm_save_keeps_dsm_fields():
    # the DSM saved the ingest before the import: its interval and enabled stay
    conn = FakeDB(
        ingests={U1: 1},
        configs={1: (30, False)},
        schedules={1: ["33-59/30 * * * *", 17, False, 30]},
    )
    seen = []
    real = conn.execute

    def spy(sql, params=None):
        seen.append(sql)
        return real(sql, params)

    conn.execute = spy
    summary = legacy.import_legacy(conn, f"5 * * * * {CMD} sync-thing {U1}\n")
    assert summary.imported == 1
    assert conn.schedules[1] == ["5-59/30 * * * *", 0, False, 30]
    insert = next(s for s in seen if "INSERT INTO dsm_db.ingest_schedule" in s)
    on_conflict = insert.split("DO UPDATE")[1]
    assert "enabled" not in on_conflict and "sync_interval" not in on_conflict


def test_import_sync_thing_prefers_active_line():
    conn = FakeDB(ingests={U1: 1}, configs={1: (60, True)})
    text = (
        f"# 1 * * * * sleep 1 && {CMD} sync-thing {U1}\n"
        f"5 * * * * sleep 5 && {CMD} sync-thing {U1}\n"
        f"# 9 * * * * sleep 9 && {CMD} sync-thing {U1}\n"
    )
    summary = legacy.import_legacy(conn, text)
    assert (summary.imported, summary.skipped) == (1, 2)
    assert conn.schedules[1] == ["5 * * * *", 5, True, 60]


def test_import_sync_thing_unadaptable_keeps_line(monkeypatch):
    def fail(expression, interval):
        raise ValueError("bad")

    monkeypatch.setattr(legacy, "update_cron_expression", fail)
    conn = FakeDB(ingests={U1: 1}, configs={1: (60, True)})
    summary = legacy.import_legacy(conn, f"5 * * * * {CMD} sync-thing {U1}\n")
    assert summary.imported == 1
    assert conn.schedules[1] == ["5 * * * *", 0, True, 60]


def test_import_duplicate_jobs_prefer_active():
    conn = FakeDB(ingests={U1: 1})
    text = (
        f"# 0 4 * * MON {CMD} resync-range {U1} --days 8\n"
        f"0 4 * * MON {CMD} resync-range {U1} --days 8\n"
        f"0 5 * * MON {CMD} resync-range {U1} --days 8\n"
    )
    summary = legacy.import_legacy(conn, text)
    assert (summary.imported, summary.skipped) == (2, 1)
    assert [(j["expr"], j["enabled"]) for j in conn.jobs] == [
        ("0 4 * * MON", True),
        ("0 5 * * MON", True),
    ]
