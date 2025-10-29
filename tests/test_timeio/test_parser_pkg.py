#!/usr/bin/env python3


import pytest

from timeio.parser import (
    get_parser,
    CsvParser,
    JsonParser,
    CampbellCr6Parser,
    BrightskyDwdApiParser,
    YdocMl417Parser,
    ChirpStackGenericParser,
    SineDummyParser,
    AbcParser,
)


@pytest.mark.parametrize(
    "parser_type, has_settings, expected",
    [
        ("csvparser", True, CsvParser),
        ("jsonparser", True, JsonParser),
        ("campbell_cr6", False, CampbellCr6Parser),
        ("brightsky_dwd_api", False, BrightskyDwdApiParser),
        ("ydoc_ml417", False, YdocMl417Parser),
        ("chirpstack_generic", False, ChirpStackGenericParser),
        ("sine_dummy", False, SineDummyParser),
    ],
)
def test__get_parser__type(parser_type, has_settings, expected):
    parser = get_parser(parser_type, {})
    assert isinstance(parser, AbcParser)
    assert isinstance(parser, expected)
    if has_settings:
        assert hasattr(parser, "settings")
        assert isinstance(parser.settings, dict)


def test__get_parser__unknown_type():
    with pytest.raises(NotImplementedError, match="parser .* not known$"):
        get_parser("NonExistentType", {})


CSV_DEFAULT_SETTINGS = {
    "comment": "#",
    "decimal": ".",
    "na_values": None,
    "encoding": "utf-8",
    "engine": "python",
    "on_bad_lines": "warn",
    "header": None,
}

JSON_DEFAULT_SETTINGS = {
    "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
}


@pytest.mark.parametrize(
    "parser_type, settings, expected",
    [
        ("csvparser", {}, CSV_DEFAULT_SETTINGS),
        ("csvparser", None, CSV_DEFAULT_SETTINGS),
        ("csvparser", {"newkey": "spam"}, CSV_DEFAULT_SETTINGS | {"newkey": "spam"}),
        ("csvparser", {"header": "new"}, CSV_DEFAULT_SETTINGS | {"header": "new"}),
        (
            "csvparser",
            {"pandas_read_csv": {"newkey": "spam"}},
            CSV_DEFAULT_SETTINGS | {"newkey": "spam"},
        ),
        (
            "csvparser",
            {"pandas_read_csv": {"header": "new"}},
            CSV_DEFAULT_SETTINGS | {"header": "new"},
        ),
        (
            "csvparser",
            {"header": "b", "pandas_read_csv": {"header": "a"}},
            CSV_DEFAULT_SETTINGS | {"header": "b"},
        ),
        # JSON PARSER
        ("jsonparser", {}, JSON_DEFAULT_SETTINGS),
        ("jsonparser", None, JSON_DEFAULT_SETTINGS),
        ("jsonparser", {"newkey": "spam"}, JSON_DEFAULT_SETTINGS | {"newkey": "spam"}),
        ("jsonparser", {"header": "new"}, JSON_DEFAULT_SETTINGS | {"header": "new"}),
        # TODO: is pandas_json_normalize really a dictionary, or just a parameter?
        # (
        #         "jsonparser",
        #         {"pandas_json_normalize": {"newkey": "spam"}},
        #         JSON_DEFAULT_SETTINGS | {"newkey": "spam"},
        # ),
        # (
        #         "jsonparser",
        #         {"pandas_json_normalize": {"header": "new"}},
        #         JSON_DEFAULT_SETTINGS | {"header": "new"},
        # ),
        # (
        #         "jsonparser",
        #         {"header": "b", "pandas_json_normalize": {"header": "a"}},
        #         JSON_DEFAULT_SETTINGS | {"header": "b"},
        # ),
    ],
)
def test__get_parser__settings(parser_type, settings, expected):
    parser = get_parser(parser_type, settings)
    assert parser.settings == expected
