#!/usr/bin/env python3

from unittest.mock import MagicMock, patch

import pytest

import run_reparse_files
from run_reparse_files import ReparseFilesManager


@pytest.fixture
def manager():
    m = ReparseFilesManager.__new__(ReparseFilesManager)
    m.dsmdb_dsn = "dsn"
    m.minio = MagicMock()
    m.mqtt_broker = "broker:1883"
    m.mqtt_user = "user"
    m.mqtt_password = "pw"
    m.mqtt_client_id = "reparse-files"
    return m


@pytest.fixture
def mocks():
    with patch.object(run_reparse_files, "Thing") as thing, patch.object(
        run_reparse_files, "parser_exists"
    ) as parser_exists, patch.object(
        run_reparse_files, "make_publisher"
    ) as make_publisher, patch.object(
        run_reparse_files, "reparse_files"
    ) as reparse_files, patch.object(
        run_reparse_files, "journal"
    ) as journal:
        thing.from_uuid.return_value = MagicMock(uuid="thing-uuid")
        parser_exists.return_value = True
        yield MagicMock(
            Thing=thing,
            parser_exists=parser_exists,
            make_publisher=make_publisher,
            reparse_files=reparse_files,
            journal=journal,
        )


CONTENT = {
    "version": 1,
    "thing": "thing-uuid",
    "include_parsed": False,
    "parsed_files_parser": "current",
}


def test_minimal_message_uses_defaults(manager, mocks):
    manager.act(dict(CONTENT), MagicMock())

    mocks.Thing.from_uuid.assert_called_once_with("thing-uuid", dsn="dsn")
    thing = mocks.Thing.from_uuid.return_value
    publisher = mocks.make_publisher.return_value
    mocks.reparse_files.assert_called_once_with(
        thing,
        manager.minio,
        publisher,
        mocks.journal,
        "dsn",
        start_date=None,
        end_date=None,
        filename_pattern=None,
        parser_uuid=None,
        include_parsed=False,
        parsed_files_parser="current",
    )
    mocks.parser_exists.assert_not_called()


def test_all_options_are_passed_on(manager, mocks):
    content = {
        **CONTENT,
        "start_date": "2026-01-01",
        "end_date": "2026-02-01",
        "filename_pattern": "*.csv",
        "parser_uuid": "P",
        "include_parsed": True,
        "parsed_files_parser": "original",
    }

    manager.act(content, MagicMock())

    mocks.parser_exists.assert_called_once_with("P", "dsn")
    kwargs = mocks.reparse_files.call_args.kwargs
    assert kwargs == {
        "start_date": "2026-01-01",
        "end_date": "2026-02-01",
        "filename_pattern": "*.csv",
        "parser_uuid": "P",
        "include_parsed": True,
        "parsed_files_parser": "original",
    }


def test_publisher_uses_own_client_id_and_credentials(manager, mocks):
    manager.act(dict(CONTENT), MagicMock())

    mocks.make_publisher.assert_called_once_with(
        "broker:1883", "user", "pw", "reparse-files-publisher"
    )


def test_publisher_is_stopped_after_a_successful_run(manager, mocks):
    manager.act(dict(CONTENT), MagicMock())

    publisher = mocks.make_publisher.return_value
    publisher.loop_stop.assert_called_once()
    publisher.disconnect.assert_called_once()


def test_missing_parser_stops_before_any_work_and_journals_error(manager, mocks):
    mocks.parser_exists.return_value = False

    manager.act({**CONTENT, "parser_uuid": "GONE"}, MagicMock())

    mocks.make_publisher.assert_not_called()
    mocks.reparse_files.assert_not_called()
    mocks.journal.error.assert_called_once()
    message, thing_uuid = mocks.journal.error.call_args.args
    assert "GONE" in message
    assert thing_uuid == "thing-uuid"


def test_error_in_run_is_journalled_reraised_and_publisher_is_stopped(manager, mocks):
    mocks.reparse_files.side_effect = RuntimeError("minio down")

    with pytest.raises(RuntimeError, match="minio down"):
        manager.act(dict(CONTENT), MagicMock())

    mocks.journal.error.assert_called_once()
    message, thing_uuid = mocks.journal.error.call_args.args
    assert "aborted" in message and "minio down" in message
    assert thing_uuid == "thing-uuid"
    publisher = mocks.make_publisher.return_value
    publisher.loop_stop.assert_called_once()
    publisher.disconnect.assert_called_once()
