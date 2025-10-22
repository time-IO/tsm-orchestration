import pytest
import uuid
from unittest.mock import MagicMock, patch
from setup_crontab import CreateThingInCrontabHandler

class Project:
    def __init__(self, name):
        self.name = name

BASE_THING_ATTRS = {
    "uuid": str(uuid.uuid4()),
    "name": "thing-name",
    "project": Project(name="project-name"),
}

def make_thing(**overrides):
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
    thing = make_thing(ext_sftp=ext_sftp, ext_api=ext_api)
    job = MagicMock()
    info = CreateThingInCrontabHandler.make_job(job, thing)
    assert info.startswith(expected_in_info)

def test_make_job_no_external_sftp_or_api():
    thing = make_thing(ext_sftp=None, ext_api=None)
    job = MagicMock()
    info = CreateThingInCrontabHandler.make_job(job, thing)
    assert info == ""
    job.set_command.assert_not_called()
    job.enable.assert_not_called()

def test_update_job_ext_sftp():
    ext_sftp = MagicMock(sync_interval=30, sync_enabled=True, uri="sftp://make:22")
    thing = make_thing(ext_sftp=ext_sftp, ext_api=None)
    job = MagicMock()
    CreateThingInCrontabHandler.make_job(job, thing)
    ext_sftp_update = MagicMock(sync_interval=120, sync_enabled=False, uri="sftp://update:22")
    thing_update = make_thing(ext_sftp=ext_sftp_update, ext_api=None)
    CreateThingInCrontabHandler.update_job(job, thing_update)
    assert job.enable.call_args_list[0][1]['enabled'] is True
    assert thing.uuid in job.set_command.call_args_list[0][0][0]
    assert job.enable.call_args_list[1][1]['enabled'] is False
    assert thing.uuid in job.set_command.call_args_list[1][0][0]

def test_update_job_ext_api():
    ext_api = MagicMock(interval=30, enabled=True, api_type_name="MakeAPI")
    thing = make_thing(ext_api=ext_api, ext_sftp=None)
    job = MagicMock()
    CreateThingInCrontabHandler.make_job(job, thing)
    ext_api_update = MagicMock(interval=120, enabled=False, api_type_name="UpdateAPI")
    thing_update = make_thing(ext_api=ext_api_update, ext_sftp=None)
    CreateThingInCrontabHandler.update_job(job, thing_update)
    assert job.enable.call_args_list[0][1]['enabled'] is True
    assert thing.uuid in job.set_command.call_args_list[0][0][0]
    assert job.enable.call_args_list[1][1]['enabled'] is False
    assert thing.uuid in job.set_command.call_args_list[1][0][0]  #assert info == ""