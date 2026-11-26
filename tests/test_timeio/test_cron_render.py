from datetime import datetime

import pytest

from timeio.cron import jobs, legacy, schedule

U1 = "00000000-0000-0000-0000-000000000001"
U2 = "00000000-0000-0000-0000-000000000002"
TS = datetime(2026, 1, 2, 3, 4, 5)
CMD = "python3 /scripts/mqtt_sync_wrapper.py"
SUFFIX = "> $STDOUT 2> $STDERR"


def sched(ingest_id=1, uuid=U1, expr="5-59/10 * * * *", jitter=7, enabled=True, **kw):
    return jobs.ScheduleRow(
        ingest_id, uuid, kw.get("name", "thing"), kw.get("project", "proj"),
        expr, jitter, enabled, TS,
    )  # fmt: skip


def job(id=1, job_type="resync_thing", uuid=U1, params=None, **kw):
    return jobs.JobRow(
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
        ("sync_sms", None, {"origin": "sms_cv"}, "sync-sms sms_cv"),
        ("mqtt_monitoring", None, {}, "mqtt-monitoring"),
    ],
)
def test_build_command(job_type, target, params, args):
    assert (
        jobs.build_command(job_type, target, params, 5)
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
        ("mqtt_monitoring", None, {"x": 1}, 0),
    ],
)
def test_build_command_rejects(job_type, target, params, jitter):
    with pytest.raises(ValueError):
        jobs.build_command(job_type, target, params, jitter)


@pytest.mark.parametrize(
    ("expr", "valid"),
    [
        ("*/5 * * * *", True),
        ("0 3 * * 0", True),
        ("0  4 * * MON", True),
        ("* * * * * *", False),
        ("@daily", False),
        ("61 * * * *", False),
        ("", False),
    ],
)
def test_validate_expression(expr, valid):
    assert schedule.validate_expression(expr) is valid


def test_render_format_and_order():
    text = jobs.render_crontab(
        [sched(2, U2, name="b"), sched(1, U1, jitter=0, enabled=False)],
        [job(5, "sync_sms", None, {"origin": "sms_cv"}, name=None, note="x")],
    )
    assert text == (
        f"# 2026-01-02 03:04:05 | proj | thing | {U1}\n"
        f"# 5-59/10 * * * * sleep 0 && {CMD} sync-thing {U1} {SUFFIX}\n"
        "\n"
        f"# 2026-01-02 03:04:05 | proj | b | {U2}\n"
        f"5-59/10 * * * * sleep 7 && {CMD} sync-thing {U2} {SUFFIX}\n"
        "\n"
        "# 2026-01-02 03:04:05 | sync_sms | sms_cv | x\n"
        f"0 3 * * 0 sleep 0 && {CMD} sync-sms sms_cv {SUFFIX}\n"
    )


def test_render_is_deterministic():
    a = jobs.render_crontab([sched(1), sched(2, U2)], [job(1), job(2)])
    b = jobs.render_crontab([sched(2, U2), sched(1)], [job(2), job(1)])
    assert a == b


def test_render_skips_invalid_rows():
    skipped = []
    text = jobs.render_crontab(
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
    text = jobs.render_crontab([sched(name="a\nb")], [])
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
    parsed = legacy.parse_legacy_crontab(LEGACY)
    kinds = [(j.kind, j.target, j.days, j.jitter, j.enabled) for j in parsed.jobs]
    assert kinds == [
        ("mqtt_monitoring", None, None, 0, True),
        ("sync_thing", U1, None, 12, True),
        ("sync_thing", U2, None, 0, False),
        ("resync_thing", U1, 14, 0, True),
        ("resync_thing", U2, 7, 0, True),
        ("sync_sms", "sms_backend", None, 0, True),
    ]
    assert parsed.jobs[0].expression == "*/30 * * * * * *"
    assert parsed.jobs[1].expression == "5-59/10 * * * *"
    # commented-out cron lines are reported, plain comments are not
    assert [n for n, _ in parsed.unknown] == [1, 9, 10]


@pytest.mark.parametrize(
    ("line", "unknown"),
    [
        ("# 0 0 * * * /usr/bin/x", True),
        ("#*/30 * * * * * * /usr/bin/x", True),
        ("# mqtt monitoring", False),
        (f"# 2026-01-01 00:00:00 | proj | thing | {U1}", False),
        ("# 0 0 * * *", False),
    ],
)
def test_parse_legacy_commented_lines(line, unknown):
    assert bool(legacy.parse_legacy_crontab(line + "\n").unknown) is unknown


def test_parse_legacy_seven_field_resync_is_unknown():
    parsed = legacy.parse_legacy_crontab(
        f"* * * * * * * {CMD} resync-range {U1} {SUFFIX}\n"
    )
    assert not parsed.jobs and len(parsed.unknown) == 1


@pytest.mark.parametrize(
    ("command", "expected"),
    [("sleep 12 && python3 x", 12), ("sleep 99 && x", 59), ("python3 x", None)],
)
def test_jitter_from_command(command, expected):
    assert legacy.jitter_from_command(command) == expected


def test_render_normalizes_whitespace_and_rejects_bad_params():
    skipped = []
    text = jobs.render_crontab(
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
    parsed = legacy.parse_legacy_crontab(f"0 * * * * {CMD} {args} {SUFFIX}\n")
    assert not parsed.jobs and len(parsed.unknown) == 1


def test_parse_legacy_accepts_days_equals_and_uppercase_uuid():
    text = (
        f"0 * * * * {CMD} resync-range {U1.upper()} --days=30 {SUFFIX}\n"
        f"0 * * * * {CMD} resync-range {U2} --days 365 {SUFFIX}\n"
    )
    parsed = legacy.parse_legacy_crontab(text).jobs
    assert [(j.target, j.days) for j in parsed] == [(U1, 30), (U2, 365)]


@pytest.mark.parametrize("job_type", ["sync_thing", "resync_project"])
def test_render_skips_unknown_job_types(job_type):
    skipped = []
    text = jobs.render_crontab([], [job(job_type=job_type)], on_skip=skipped.append)
    assert "sync-thing" not in text and len(skipped) == 1


@pytest.mark.parametrize(
    ("expr", "allow_seconds", "valid"),
    [
        ("*/30 * * * * * *", True, True),
        ("*/30 * * * * * *", False, False),
        ("0 0 4 * * MON *", True, True),
        ("60 * * * * * *", True, False),
        ("*/30 * * * * * 20x", True, False),
        ("* * * * * *", True, False),
        ("0 4 * * MON", False, True),
    ],
)
def test_validate_expression_seconds(expr, allow_seconds, valid):
    assert schedule.validate_expression(expr, allow_seconds) is valid


def test_render_mqtt_monitoring_seven_fields():
    text = jobs.render_crontab(
        [], [job(1, "mqtt_monitoring", None, {}, name=None, expr="*/30 * * * * * *")]
    )
    assert f"\n*/30 * * * * * * sleep 0 && {CMD} mqtt-monitoring {SUFFIX}\n" in text


PROD_SHAPES = f"""\
*/30 * * * * * * /scripts/mqtt_sync_wrapper.py mqtt-monitoring > $STDOUT 2>$STDERR
0 4 * * MON /scripts/mqtt_sync_wrapper resync-range {U1} --days 8 > $STDOUT 2>$STDERR
5-59 * * * * python3 /scripts/mqtt_sync_wrapper.py sync-sms sms_backend 2>&1
# 30 1 * * * python3 /scripts/mqtt_sync_wrapper.py sync-sms sms_cv
# 0 * * * * python3 /scripts/trigger_qaqc.py {U1}
"""


def test_parse_legacy_prod_shapes():
    parsed = legacy.parse_legacy_crontab(PROD_SHAPES)
    assert [
        (j.kind, j.target, j.days, j.expression, j.enabled) for j in parsed.jobs
    ] == [
        ("mqtt_monitoring", None, None, "*/30 * * * * * *", True),
        ("resync_thing", U1, 8, "0 4 * * MON", True),
        ("sync_sms", "sms_backend", None, "5-59 * * * *", True),
        ("sync_sms", "sms_cv", None, "30 1 * * *", False),
    ]
    assert [n for n, _ in parsed.unknown] == [5]


QC = "python3 /scripts/trigger_qaqc.py"


@pytest.mark.parametrize(
    ("name", "quoted"),
    [("My QC", "'My QC'"), ("plain", "plain"), ("it's", "'it'\"'\"'s'")],
)
def test_build_command_trigger_qc(name, quoted):
    command = jobs.build_command("trigger_qc", U1, {"interval": "1h"}, 3, name)
    assert command == (
        f"sleep 3 && {QC} --interval 1h --project-uuid {U1} "
        f"--qc-settings-name {quoted} {SUFFIX}"
    )


@pytest.mark.parametrize(
    ("params", "name"),
    [
        ({"interval": "1 h"}, "x"),
        ({"interval": "0h"}, "x"),
        ({"interval": "1w"}, "x"),
        ({}, "x"),
        ({"interval": "1h"}, None),
        ({"interval": "1h"}, "a\nb"),
    ],
)
def test_build_command_trigger_qc_rejects(params, name):
    with pytest.raises(ValueError):
        jobs.build_command("trigger_qc", U1, params, 0, name)


def test_render_trigger_qc():
    row = job(5, "trigger_qc", U2, {"interval": "1d"}, name="grp / My QC", note="n")
    row.qc_settings_name = "My QC"
    text = jobs.render_crontab([], [row])
    assert text == (
        "# 2026-01-02 03:04:05 | trigger_qc | grp / My QC | n\n"
        f"0 3 * * 0 sleep 0 && {QC} --interval 1d --project-uuid {U2} "
        f"--qc-settings-name 'My QC' {SUFFIX}\n"
    )


def test_render_trigger_qc_without_setting_is_skipped():
    skipped = []
    jobs.render_crontab(
        [], [job(5, "trigger_qc", U2, {"interval": "1d"})], skipped.append
    )
    assert len(skipped) == 1


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (
            f"0 * * * * python3 /scripts/trigger_qaqc.py --interval 1h "
            f"--project-uuid {U1} --qc-settings-name 'My QC' {SUFFIX}",
            ("My QC", "1h", "0 * * * *", True),
        ),
        (
            f"# 0 2 * * * /scripts/trigger_qaqc.py --project-uuid={U1} "
            "--qc-settings-name x --interval=1d",
            ("x", "1d", "0 2 * * *", False),
        ),
    ],
)
def test_parse_legacy_trigger_qc(line, expected):
    parsed = legacy.parse_legacy_crontab(line + "\n")
    assert not parsed.unknown
    (j,) = parsed.jobs
    assert (j.kind, j.target) == ("trigger_qc", U1)
    assert (j.qc_name, j.qc_interval, j.expression, j.enabled) == expected


@pytest.mark.parametrize(
    "args",
    [
        f"--interval 1h --project-uuid {U1}",
        f"--interval 1h --project-uuid {U1} --qc-settings-name x --extra y",
        f"--interval 1h --project-uuid nope --qc-settings-name x",
        f"--interval 1 --project-uuid {U1} --qc-settings-name x",
        f"--interval 1h --project-uuid {U1} --qc-settings-name 'x",
    ],
)
def test_parse_legacy_trigger_qc_unknown(args):
    parsed = legacy.parse_legacy_crontab(f"0 * * * * {QC} {args}\n")
    assert not parsed.jobs and len(parsed.unknown) == 1


def test_render_expands_macros():
    text = jobs.render_crontab(
        [sched(expr="@daily")], [job(expr="@weekly"), job(2, expr="@reboot")]
    )
    assert f"\n0 0 * * * sleep 7 && {CMD} sync-thing {U1}" in text
    assert "\n0 0 * * 0 " in text and "@" not in text.replace("$", "")


def test_parse_legacy_macros():
    parsed = legacy.parse_legacy_crontab(
        f"@hourly {CMD} resync-range {U1} {SUFFIX}\n"
        f"# @DAILY sleep 3 && {CMD} sync-sms sms_cv\n"
        f"@reboot {CMD} resync-range {U1}\n"
        f"@weekly {QC} --interval 7d --project-uuid {U1} --qc-settings-name x\n"
        "# @hourly /usr/bin/x\n"
    )
    assert [(j.kind, j.expression, j.jitter, j.enabled) for j in parsed.jobs] == [
        ("resync_thing", "0 * * * *", 0, True),
        ("sync_sms", "0 0 * * *", 3, False),
        ("trigger_qc", "0 0 * * 0", 0, True),
    ]
    assert [n for n, _ in parsed.unknown] == [3, 5]
