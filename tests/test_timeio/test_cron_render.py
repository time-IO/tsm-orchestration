from datetime import datetime

import pytest

from timeio import cron

U1 = "00000000-0000-0000-0000-000000000001"
U2 = "00000000-0000-0000-0000-000000000002"
TS = datetime(2026, 1, 2, 3, 4, 5)
CMD = "python3 /scripts/mqtt_sync_wrapper.py"
SUFFIX = "> $STDOUT 2> $STDERR"


def sched(ingest_id=1, uuid=U1, expr="5-59/10 * * * *", jitter=7, enabled=True, **kw):
    return cron.ScheduleRow(
        ingest_id, uuid, kw.get("name", "thing"), kw.get("project", "proj"),
        expr, jitter, enabled, TS,
    )  # fmt: skip


def job(id=1, job_type="resync_thing", uuid=U1, params=None, **kw):
    return cron.JobRow(
        id, job_type, uuid, kw.get("name", "thing"),
        params if params is not None else {"days": 7},
        kw.get("expr", "0 3 * * 0"), kw.get("jitter", 0), kw.get("enabled", True),
        kw.get("note", "weekly"), TS,
    )  # fmt: skip


@pytest.mark.parametrize(
    ("job_type", "target", "params", "args"),
    [
        ("sync_thing", U1, None, f"sync-thing {U1}"),
        ("resync_thing", U1, {"days": 3}, f"resync-range {U1} --days 3"),
        ("resync_project", U1, {}, f"resync-project {U1} --days 7"),
        ("sync_sms", None, {"origin": "sms_cv"}, "sync-sms sms_cv"),
    ],
)
def test_build_command(job_type, target, params, args):
    assert (
        cron.build_command(job_type, target, params, 5)
        == f"sleep 5 && {CMD} {args} {SUFFIX}"
    )


@pytest.mark.parametrize(
    ("job_type", "target", "params", "jitter"),
    [
        ("sync_sms", None, {"origin": "x; rm -rf /"}, 0),
        ("sync_thing", "1; rm -rf /", None, 0),
        ("resync_thing", U1, {"days": 0}, 0),
        ("resync_thing", U1, {"days": "7"}, 0),
        ("sync_thing", U1, None, 60),
        ("unknown", U1, None, 0),
    ],
)
def test_build_command_rejects(job_type, target, params, jitter):
    with pytest.raises(ValueError):
        cron.build_command(job_type, target, params, jitter)


@pytest.mark.parametrize(
    ("expr", "valid"),
    [
        ("*/5 * * * *", True),
        ("0 3 * * 0", True),
        ("* * * * * *", False),
        ("@daily", False),
        ("61 * * * *", False),
        ("", False),
    ],
)
def test_validate_expression(expr, valid):
    assert cron.validate_expression(expr) is valid


def test_render_format_and_order():
    text = cron.render_crontab(
        [sched(2, U2, name="b"), sched(1, U1, jitter=0, enabled=False)],
        [job(5, "sync_sms", None, {"origin": "sms_cv"}, name=None, note="x")],
        "# static\n* * * * * * * echo hi\n",
    )
    assert text == (
        "# static\n* * * * * * * echo hi\n\n"
        f"# 2026-01-02 03:04:05 | proj | thing | {U1}\n"
        f"# 5-59/10 * * * * sleep 0 && {CMD} sync-thing {U1} {SUFFIX}\n"
        f"# 2026-01-02 03:04:05 | proj | b | {U2}\n"
        f"5-59/10 * * * * sleep 7 && {CMD} sync-thing {U2} {SUFFIX}\n"
        "# 2026-01-02 03:04:05 | sync_sms | sms_cv | x\n"
        f"0 3 * * 0 sleep 0 && {CMD} sync-sms sms_cv {SUFFIX}\n"
    )


def test_render_is_deterministic():
    a = cron.render_crontab([sched(1), sched(2, U2)], [job(1), job(2)])
    b = cron.render_crontab([sched(2, U2), sched(1)], [job(2), job(1)])
    assert a == b


def test_render_skips_invalid_rows():
    skipped = []
    text = cron.render_crontab(
        [sched(1, expr="nope"), sched(2, U2)],
        [
            job(1, params={"days": 999}),
            job(2, "sync_sms", None, {"origin": "a;b"}),
            job(3, "bogus"),
            job(4, expr="* * * * * *"),
        ],
        on_skip=skipped.append,
    )
    assert len(skipped) == 5
    assert text.count("python3") == 1 and U2 in text


def test_render_sanitizes_comment_newlines():
    text = cron.render_crontab([sched(name="a\nb")], [])
    assert "| a b |" in text and text.count("\n") == 2


LEGACY = f"""\
# * * * * * /place-sms-and-other-manual-commands-here.sh
*/30 * * * * * * python3 /scripts/mqtt_sync_wrapper.py mqtt-monitoring > $STDOUT 2> $STDERR
# 2026-01-01 00:00:00 | proj | thing | {U1}
5-59/10 * * * * sleep 12 && {CMD} sync-thing {U1} {SUFFIX}
# 0-59/5 * * * * {CMD} sync-thing {U2} {SUFFIX}
0 3 * * 0 {CMD} resync-range {U1} --days 14 {SUFFIX}
0 4 * * 0 {CMD} resync-range {U2} {SUFFIX}
10 * * * * {CMD} sync-sms sms_backend {SUFFIX}
10 * * * * {CMD} sync-sms evil {SUFFIX}
0 0 * * * /usr/bin/something-else
"""


def test_parse_legacy_crontab():
    legacy = cron.parse_legacy_crontab(LEGACY)
    kinds = [(j.kind, j.target, j.days, j.jitter, j.enabled) for j in legacy.jobs]
    assert kinds == [
        ("mqtt_monitoring", None, None, 0, True),
        ("sync_thing", U1, None, 12, True),
        ("sync_thing", U2, None, 0, False),
        ("resync_thing", U1, 14, 0, True),
        ("resync_thing", U2, 7, 0, True),
        ("sync_sms", "sms_backend", None, 0, True),
    ]
    assert legacy.jobs[1].expression == "5-59/10 * * * *"
    assert [n for n, _ in legacy.unknown] == [9, 10]


def test_parse_legacy_seven_field_sync_is_unknown():
    legacy = cron.parse_legacy_crontab(
        f"* * * * * * * {CMD} sync-thing {U1} {SUFFIX}\n"
    )
    assert not legacy.jobs and len(legacy.unknown) == 1


@pytest.mark.parametrize(
    ("command", "expected"),
    [("sleep 12 && python3 x", 12), ("sleep 99 && x", 59), ("python3 x", None)],
)
def test_jitter_from_command(command, expected):
    assert cron.jitter_from_command(command) == expected


def test_render_normalizes_whitespace_and_rejects_bad_params():
    skipped = []
    text = cron.render_crontab(
        [sched(expr="5-59/10  * * *\t*")],
        [job(1, params=[]), job(2, "sync_sms", None, "x")],
        on_skip=skipped.append,
    )
    assert f"\n5-59/10 * * * * sleep 7 && {CMD}" in text
    assert len(skipped) == 2 and text.count("python3") == 1


@pytest.mark.parametrize(
    "args",
    [
        f"sync-thing {U1} extra",
        f"resync-range {U1} --days=30x",
        f"resync-range {U1} --days 0",
        f"resync-range {U1} --days 366",
        f"resync-range {U1} --days",
        f"resync-range --days 3 {U1}",
        "sync-sms sms_cv --foo",
    ],
)
def test_parse_legacy_rejects_unexpected_args(args):
    legacy = cron.parse_legacy_crontab(f"0 * * * * {CMD} {args} {SUFFIX}\n")
    assert not legacy.jobs and len(legacy.unknown) == 1


def test_parse_legacy_accepts_days_equals_and_uppercase_uuid():
    text = (
        f"0 * * * * {CMD} resync-range {U1.upper()} --days=30 {SUFFIX}\n"
        f"0 * * * * {CMD} resync-range {U2} --days 365 {SUFFIX}\n"
    )
    jobs = cron.parse_legacy_crontab(text).jobs
    assert [(j.target, j.days) for j in jobs] == [(U1, 30), (U2, 365)]


def test_render_custom_sync_thing_job():
    text = cron.render_crontab([], [job(job_type="sync_thing", params={})])
    assert f"0 3 * * 0 sleep 0 && {CMD} sync-thing {U1} {SUFFIX}" in text


def test_validate_params_sync_thing_has_none():
    assert cron.validate_params("sync_thing", {"days": 3}) == {}
