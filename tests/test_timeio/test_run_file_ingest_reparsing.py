#!/usr/bin/env python3

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from timeio.feta import ObjectNotFound
from run_file_ingest import ParserJobHandler

CURRENT = "current-parser-uuid"
CHOSEN = "chosen-parser-uuid"
OLD = "old-parser-uuid"


def make_pobj(uuid, type_name="csv"):
    return SimpleNamespace(
        uuid=uuid,
        file_parser_type=SimpleNamespace(name=type_name),
        params={"encoding": "utf-8", "delimiter": ","},
    )


def make_message(**extra):
    return {
        "EventName": "s3:ObjectCreated:Put",
        "Key": "bucket/data.csv",
        **extra,
    }


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
        file_parser.from_id.return_value = s.current
        s.Thing, s.FileParser, s.get_parser, s.journal = (
            thing,
            file_parser,
            get_parser,
            journal,
        )
        yield s


def test_reparsing_with_parser_uuid_uses_that_parser(setup):
    setup.FileParser.from_uuid.return_value = make_pobj(CHOSEN, "json")

    setup.handler.act(make_message(reparsing=True, parser_uuid=CHOSEN), MagicMock())

    setup.FileParser.from_uuid.assert_called_once_with(CHOSEN, dsn="dsn")
    # the parser object is built from the chosen record, not from the current one
    assert setup.get_parser.call_args.args[0] == "json"
    # and label and parser agree
    assert setup.parser.to_observations.call_args.args[2] == CHOSEN
    setup.handler.set_tags.assert_called_once_with(
        "bucket", "data.csv", CHOSEN, "successful"
    )


def test_reparsing_without_parser_uuid_uses_current_parser(setup):
    setup.handler.act(make_message(reparsing=True), MagicMock())

    setup.FileParser.from_uuid.assert_not_called()
    assert setup.get_parser.call_args.args[0] == "csv"
    assert setup.parser.to_observations.call_args.args[2] == CURRENT
    setup.handler.set_tags.assert_called_once_with(
        "bucket", "data.csv", CURRENT, "successful"
    )


@pytest.mark.parametrize("parser_uuid", [None, CHOSEN])
def test_reparsing_never_reads_the_file_tags(setup, parser_uuid):
    setup.FileParser.from_uuid.return_value = make_pobj(CHOSEN)
    extra = {"parser_uuid": parser_uuid} if parser_uuid else {}

    setup.handler.act(make_message(reparsing=True, **extra), MagicMock())

    setup.handler.get_parser_tags.assert_not_called()


def test_reparsing_stores_observations_and_triggers_data_parsed(setup):
    setup.handler.act(make_message(reparsing=True), MagicMock())

    setup.handler.dbapi.upsert_observations_and_datastreams.assert_called_once_with(
        "thing-uuid", [{"result": 1}], mutable=False
    )
    publish = setup.handler.mqtt_client.publish
    assert publish.call_args.kwargs["topic"] == "data_parsed"


def test_reparsing_with_missing_parser_does_not_parse_and_warns(setup):
    setup.FileParser.from_uuid.side_effect = ObjectNotFound("gone")

    setup.handler.act(make_message(reparsing=True, parser_uuid=CHOSEN), MagicMock())

    setup.get_parser.assert_not_called()
    setup.handler.read_file.assert_not_called()
    setup.handler.dbapi.upsert_observations_and_datastreams.assert_not_called()
    setup.handler.set_tags.assert_not_called()  # the old tag stays untouched
    setup.handler.mqtt_client.publish.assert_not_called()
    setup.journal.warning.assert_called_once()
    message, thing_uuid = setup.journal.warning.call_args.args
    assert CHOSEN in message and "data.csv" in message
    assert thing_uuid == "thing-uuid"


def test_reparsing_still_respects_the_things_filename_pattern(setup):
    content = make_message(reparsing=True)
    content["Key"] = "bucket/data.txt"

    setup.handler.act(content, MagicMock())

    setup.get_parser.assert_not_called()
    setup.handler.set_tags.assert_not_called()


def test_normal_upload_without_tag_uses_current_parser(setup):
    setup.handler.act(make_message(), MagicMock())

    setup.handler.get_parser_tags.assert_called_once_with("bucket", "data.csv")
    setup.FileParser.from_uuid.assert_not_called()
    assert setup.parser.to_observations.call_args.args[2] == CURRENT


def test_normal_upload_behaviour_with_old_tag_is_unchanged(setup):
    """Documents the existing behaviour (parser-tag ticket): the tag only decides
    the label, the parser object is still the current one."""
    setup.handler.get_parser_tags.return_value = {"parser_id": OLD}

    setup.handler.act(make_message(), MagicMock())

    setup.FileParser.from_uuid.assert_not_called()
    assert setup.get_parser.call_args.args[0] == "csv"  # current parser
    assert setup.parser.to_observations.call_args.args[2] == OLD  # label from tag
