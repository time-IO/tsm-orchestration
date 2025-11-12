# python
from datetime import datetime, timedelta

import pytest
import uuid
from unittest.mock import MagicMock
from setup_crontab import CreateThingInCrontabHandler

class JobMock:
    def __init__(self):
        self.enable_calls = []
        self.commands = []
        self.comments = []
        self.comment = ""
        self.slices = ""
        self._current_interval_min = 30

    def enable(self, *args, **kwargs):
        enabled = kwargs.get("enabled", True) if kwargs else (args[0] if args else True)
        self.enable_calls.append(enabled)

    def set_command(self, command):
        self.commands.append(str(command))

    def set_comment(self, comment, pre_comment=False):
        # keep compatibility with code that reads job.comment
        self.comment = str(comment)
        self.comments.append((str(comment), bool(pre_comment)))

    def setall(self, schedule):
        self.slices = str(schedule)

    def schedule(self):
        class ScheduleFake:
            def __init__(self, interval_min):
                self.interval = interval_min
                self._dt_now = datetime.now().replace(second=0, microsecond=0)

            # Assume we are in-between two runs for testing purposes
            def get_next(self):
                return self._dt_now + timedelta(minutes=self.interval // 2)

            def get_prev(self):
                return self._dt_now - timedelta(minutes=self.interval // 2)

        return ScheduleFake(self._current_interval_min)

class ProjectMock:
    def __init__(self, name):
        self.name = name

BASE_THING_ATTRS = {
    "uuid": str(uuid.uuid4()),
    "name": "thing-name",
    "project": ProjectMock(name="project-name"),
}

def ThingMock(**overrides):
    thing = MagicMock()
    for k, v in BASE_THING_ATTRS.items():
        setattr(thing, k, v)
    for k, v in overrides.items():
        setattr(thing, k, v)
    return thing

@pytest.mark.parametrize(
    ["ext_sftp", "ext_api", "expected_in_info"],
    [
        (
            MagicMock(sync_interval=15, sync_enabled=True, uri="sftp://test:22"),
            None,
            "sFTP sftp://test:22 @ 15m and schedule",
        ),
        (
            None,
            MagicMock(sync_interval=120, enabled=True, api_type_name="TestAPI"),
            "TestAPI-API @ 120m and schedule",
        ),
    ],
)
def test_make_job_info(ext_sftp, ext_api, expected_in_info):
    thing = ThingMock(ext_sftp=ext_sftp, ext_api=ext_api)
    job = JobMock()
    info = CreateThingInCrontabHandler.make_job(job, thing)
    assert info.startswith(expected_in_info)

def test_make_job_no_external_sftp_or_api():
    thing = ThingMock(ext_sftp=None, ext_api=None)
    job = JobMock()
    info = CreateThingInCrontabHandler.make_job(job, thing)
    assert info == ""
    assert job.commands == []
    assert job.enable_calls == []

@pytest.mark.parametrize(
    "kind, initial_kwargs, update_kwargs",
    [
        (
            "sftp",
            {"sync_interval": 30, "sync_enabled": True, "uri": "sftp://make:22"},
            {"sync_interval": 120, "sync_enabled": False, "uri": "sftp://update:22"},
        ),
        (
            "api",
            {"sync_interval": 30, "enabled": True, "api_type_name": "MakeAPI"},
            {"sync_interval": 120, "enabled": False, "api_type_name": "UpdateAPI"},
        ),
    ],
)
def test_update_job_parametrized(kind, initial_kwargs, update_kwargs):
    if kind == "sftp":
        thing_make = ThingMock(ext_api=None, ext_sftp=MagicMock(**initial_kwargs))
        thing_update = ThingMock(ext_api=None, ext_sftp=MagicMock(**update_kwargs))
    else:
        thing_make = ThingMock(ext_api=MagicMock(**initial_kwargs), ext_sftp=None)
        thing_update = ThingMock(ext_api=MagicMock(**update_kwargs), ext_sftp=None)

    # ensure update uses the same uuid (no new uuid should be generated for the update)
    thing_update.uuid = thing_make.uuid

    job = JobMock()
    # robustes Setzen mit Fallback
    job._current_interval_min = int(initial_kwargs.get("sync_interval") or initial_kwargs.get("interval") or 30)

    CreateThingInCrontabHandler.make_job(job, thing_make)
    CreateThingInCrontabHandler.update_job(job, thing_update)

    assert job.enable_calls[0] is True
    assert job.enable_calls[-1] is False

    # Prüfe, dass jede command die thing.uuid enthält
    assert job.commands, "expected at least one command"
    assert all(str(thing_update.uuid) in c for c in job.commands)

    # Prüfe, dass jedes comment die thing.uuid enthält
    assert job.comments, "expected at least one comment"
    assert all(str(thing_update.uuid) in c for c, _ in job.comments)


def test_job_belongs_to_thing_true_and_false():
    thing = ThingMock()
    job = JobMock()

    # positives Szenario: Kommentar im erwarteten Format mit der Thing-UUID
    job.set_comment(CreateThingInCrontabHandler.mk_comment(thing))
    assert CreateThingInCrontabHandler.job_belongs_to_thing(job, thing) is True

    # negatives Szenario: andere UUID im Kommentar
    job.set_comment("2025-01-01 00:00:00 | other-project | other-thing | not-the-uuid")
    assert CreateThingInCrontabHandler.job_belongs_to_thing(job, thing) is False


@pytest.mark.parametrize("interval_min", [2, 30, 60, 120, 1440, 2880])
def test_get_current_interval_returns_expected_minutes(interval_min):
    job = JobMock()
    job._current_interval_min = interval_min
    cur_int = CreateThingInCrontabHandler.get_current_interval(job)
    assert cur_int == interval_min

@pytest.mark.parametrize(
    ("schedule", "expected_base_minute"),
    [
        ("0 * * * *", 0),
        ("*/12 * * * *", 0),
        ("@daily", 0),
        ("10,30,50 * * * *", 10),
        ("7-59/12 3-23/5 * * *", 7),
    ]
)
def test_extract_base_minute(schedule, expected_base_minute):
    base_minute = CreateThingInCrontabHandler.extract_base_minute(schedule)
    assert base_minute == expected_base_minute

@pytest.mark.parametrize(
    ("old_schedule", "new_interval_min", "expect_change"),
    [
        ("*/15 * * * *", 30, True), # going form 15 to 30 minutes -> change expected
        ("16 1-23/2 * * *", 120, False), # already 2-hourly -> no change expected
        ("37 5 */2 * *", 1440, True), # going from bi-daily to daily -> change expected
        ("5,15,25,35,45,55 * * * *", 10, False),  # already every 10 minutes -> no change expected
        ("30 3-23/4 * * *", 240, False),  # no change expected
        ("56 15 * * 0", 10080, False), # already weekly -> no change expected
    ],
)
def test_update_cron_expression(old_schedule, new_interval_min, expect_change):
    job = JobMock()
    job.setall(old_schedule)
    new_schedule = CreateThingInCrontabHandler.update_cron_expression(job, new_interval_min)
    changed = new_schedule != old_schedule
    if changed:
        print(f"\n{old_schedule} -> {new_schedule} for interval {new_interval_min}m")
    assert changed == expect_change
