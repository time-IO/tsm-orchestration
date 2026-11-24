from unittest.mock import MagicMock

import pytest
from crontab import CronTab

import setup_crontab
from timeio.cron import legacy

U1 = "00000000-0000-0000-0000-000000000001"


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
    jitter = legacy.jitter_from_command(job.command)
    assert job.is_enabled()

    thing.ext_api = api(10, enabled=False)
    run_act(handler, monkeypatch, thing)
    jobs = list(CronTab(tabfile=handler.tabfile))
    assert len(jobs) == 1 and not jobs[0].is_enabled()
    assert legacy.jitter_from_command(jobs[0].command) == jitter


def test_act_without_ext_creates_nothing_and_removes_existing(handler, monkeypatch):
    thing = thing_mock()
    run_act(handler, monkeypatch, thing)
    assert not list(CronTab(tabfile=handler.tabfile))

    thing.ext_api = api()
    run_act(handler, monkeypatch, thing)
    thing.ext_api = None
    run_act(handler, monkeypatch, thing)
    assert not list(CronTab(tabfile=handler.tabfile))
