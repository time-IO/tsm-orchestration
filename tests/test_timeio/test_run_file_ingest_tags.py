#!/usr/bin/env python3

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from timeio.feta import ObjectNotFound
from run_file_ingest import ParserJobHandler

CURRENT = "current-parser-uuid"
OLD = "old-parser-uuid"


def make_pobj(uuid, type_name="csv"):
    return SimpleNamespace(
        uuid=uuid,
        file_parser_type=SimpleNamespace(name=type_name),
        params={"encoding": "utf-8", "delimiter": ","},
    )


def make_message():
    return {"EventName": "s3:ObjectCreated:Put", "Key": "bucket/data.csv"}


class Setup:
    """Handler with everything around `act()` replaced by mocks."""

    def __init__(self):
        self.current = make_pobj(CURRENT)
        self.thing = SimpleNamespace(
            uuid="thing-uuid",
            s3_store=SimpleNamespace(
                file_parser_id=1,
                filename_pattern="*.csv",
                file_parser=self.current,
            ),
            project=SimpleNamespace(database=SimpleNamespace(schema="schema")),
        )
        self.parser = MagicMock()
        self.parser.is_binary = False
        self.parser.start_date = "2026-01-01"
        self.parser.end_date = "2026-01-02"
        self.parser.do_parse.return_value = MagicMock(shape=(3, 2))
        self.parser.to_observations.return_value = [{"result": 1}]

        self.handler = ParserJobHandler.__new__(ParserJobHandler)
        self.handler.dsmdb_dsn = "dsn"
        self.handler.pub_topic = "data_parsed"
        self.handler.mqtt_qos = 1
        self.handler.mqtt_client = MagicMock()
        self.handler.dbapi = MagicMock()
        self.handler.read_file = MagicMock(return_value="a,b")
        self.handler.set_tags = MagicMock()
        self.handler.get_parser_tags = MagicMock(return_value=None)


@pytest.fixture
def setup():
    s = Setup()
    with patch("run_file_ingest.Thing") as thing, patch(
        "run_file_ingest.FileParser"
    ) as file_parser, patch(
        "run_file_ingest.get_parser", return_value=s.parser
    ) as get_parser, patch(
        "run_file_ingest.journal"
    ) as journal:
        thing.from_s3_bucket_name.return_value = s.thing
        s.Thing, s.FileParser, s.get_parser, s.journal = (
            thing,
            file_parser,
            get_parser,
            journal,
        )
        yield s


def test_upload_without_tag_uses_current_parser(setup):
    setup.handler.act(make_message(), MagicMock())

    setup.FileParser.from_uuid.assert_not_called()
    assert setup.parser.to_observations.call_args.args[2] == CURRENT
    setup.handler.set_tags.assert_called_once_with(
        "bucket", "data.csv", CURRENT, "successful"
    )


def test_upload_with_tag_uses_the_parser_from_the_tag(setup):
    setup.handler.get_parser_tags.return_value = {"parser_id": OLD}
    setup.FileParser.from_uuid.return_value = make_pobj(OLD, "json")

    setup.handler.act(make_message(), MagicMock())

    setup.FileParser.from_uuid.assert_called_once_with(OLD, dsn="dsn")
    assert setup.get_parser.call_args.args[0] == "json"
    assert setup.parser.to_observations.call_args.args[2] == OLD
    setup.handler.set_tags.assert_called_once_with(
        "bucket", "data.csv", OLD, "successful"
    )


def test_missing_parser_from_the_tag_falls_back_to_current_and_warns(setup):
    setup.handler.get_parser_tags.return_value = {"parser_id": OLD}
    setup.FileParser.from_uuid.side_effect = ObjectNotFound("gone")

    setup.handler.act(make_message(), MagicMock())

    assert setup.get_parser.call_args.args[0] == "csv"
    assert setup.parser.to_observations.call_args.args[2] == CURRENT
    setup.handler.set_tags.assert_called_once_with(
        "bucket", "data.csv", CURRENT, "successful"
    )
    setup.journal.warning.assert_called_once()
    assert OLD in setup.journal.warning.call_args.args[0]
