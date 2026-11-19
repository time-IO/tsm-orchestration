"""Predefined database records resolve through their stable implementation key."""

from unittest.mock import MagicMock, patch

import pytest

from timeio.feta import FileParser, MQTT
from timeio.parser import get_parser, TrueLog100Parser
from timeio.parser.mqtt_devices.campbell_cr6 import CampbellCr6Parser


@pytest.mark.parametrize(
    ("name", "expected"),
    [("truelog100", TrueLog100Parser), ("campbell_cr6", CampbellCr6Parser)],
)
def test_predefined_file_record_resolves_implementation_without_settings(
    name, expected
):
    record = FileParser(
        {"id": 5, "parser_type": "predefined"}, MagicMock(), caching=False
    )
    with patch.object(record, "_fetchone", return_value={"name": name}) as fetch:
        parser = get_parser(record.file_parser_type.name, record.params)
    assert isinstance(parser, expected)
    assert record.params == {}
    assert "parser_predefined" in fetch.call_args.args[1]


def test_configurable_parser_still_resolves_by_subtype():
    record = FileParser({"id": 6, "parser_type": "csv"}, MagicMock(), caching=False)
    with patch.object(record, "_get_csv_params", return_value={"delimiter": ";"}):
        assert record.file_parser_type.name == "csv"
        assert record.params == {"delimiter": ";"}


def test_mqtt_record_uses_renamed_table_and_retains_implementation_name():
    record = MQTT({"ingest_id": 7}, MagicMock(), caching=False)
    with patch.object(
        record, "_fetchone", return_value={"name": "campbell_cr6"}
    ) as fetch:
        assert record.mqtt_device_type.name == "campbell_cr6"
    assert "parser_predefined" in fetch.call_args.args[1]
