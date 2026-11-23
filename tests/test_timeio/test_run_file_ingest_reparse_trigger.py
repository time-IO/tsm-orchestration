from unittest.mock import MagicMock, patch

import pytest

import run_file_ingest
from run_file_ingest import ParserJobHandler

REPARSE_TOPIC = "reparse_files_triggered"


def trigger_message(topic=REPARSE_TOPIC):
    message = MagicMock()
    message.topic = topic
    return message


@pytest.fixture
def handler():
    h = ParserJobHandler.__new__(ParserJobHandler)
    h.dsmdb_dsn = "dsn"
    h.minio = MagicMock()
    h.mqtt_broker = "broker:1883"
    h.mqtt_user = "user"
    h.mqtt_password = "pw"
    h.mqtt_client_id = "file-ingest-triggered"
    h.reparse_topic = REPARSE_TOPIC
    return h


@pytest.fixture
def mocks():
    with patch.object(run_file_ingest, "Thing") as thing, patch.object(
        run_file_ingest, "make_publisher"
    ) as make_publisher, patch.object(
        run_file_ingest, "reparse_files"
    ) as reparse_files, patch.object(
        run_file_ingest, "reparse_journal"
    ) as journal:
        thing.from_uuid.return_value = MagicMock(uuid="thing-uuid")
        yield MagicMock(
            Thing=thing,
            make_publisher=make_publisher,
            reparse_files=reparse_files,
            journal=journal,
        )


def test_message_on_the_reparse_topic_starts_reparsing(handler, mocks):
    handler.act(
        {
            "version": 1,
            "thing": "thing-uuid",
            "include_parsed": False,
            "parsed_files_parser": "current",
        },
        trigger_message(),
    )

    mocks.reparse_files.assert_called_once()


def test_message_on_another_topic_is_not_a_reparse_trigger(handler, mocks):
    handler.is_valid_event = MagicMock(return_value=False)

    handler.act(
        {"EventName": "x"}, trigger_message("object_storage_notification_triggered")
    )

    mocks.Thing.from_uuid.assert_not_called()
    mocks.reparse_files.assert_not_called()


def test_worker_without_reparse_topic_never_reparses(mocks):
    h = ParserJobHandler.__new__(ParserJobHandler)  # reparse_topic stays None
    h.is_valid_event = MagicMock(return_value=False)

    h.act({"EventName": "x"}, trigger_message(REPARSE_TOPIC))
