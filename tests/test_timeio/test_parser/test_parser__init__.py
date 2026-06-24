#!/usr/bin/env python3


import pytest

from timeio.parser import (
    get_parser,
    CsvParser,
    JsonParser,
    CampbellCr6Parser,
    YdocMl417Parser,
    ChirpStackGenericParser,
    AbcParser,
    _default_settings,
)


@pytest.mark.parametrize(
    "parser_type, expected_type, expected_attrs",
    [
        ("csv", CsvParser, {"settings": dict}),
        ("json", JsonParser, {"settings": dict, "normalize_kws": dict}),
        ("campbell_cr6", CampbellCr6Parser, {}),
        ("ydoc_ml417", YdocMl417Parser, {}),
        ("chirpstack_generic", ChirpStackGenericParser, {}),
    ],
)
def test__get_parser__type(parser_type, expected_type, expected_attrs):
    parser = get_parser(parser_type, {})
    assert isinstance(parser, AbcParser)
    assert isinstance(parser, expected_type)
    for attr_name, typ in expected_attrs.items():
        assert hasattr(parser, attr_name)
        attr = getattr(parser, attr_name)
        assert isinstance(attr, typ)


def test__get_parser__unknown_type():
    with pytest.raises(NotImplementedError, match="parser .* not known$"):
        get_parser("NonExistentType", {})


CSV_DEFAULT_SETTINGS = _default_settings[CsvParser]
JSON_DEFAULT_SETTINGS = _default_settings[JsonParser]


@pytest.mark.parametrize(
    "parser_type, settings, expected",
    [
        ("csv", {}, CSV_DEFAULT_SETTINGS),
        ("csv", None, CSV_DEFAULT_SETTINGS),
        ("csv", {"newkey": "spam"}, CSV_DEFAULT_SETTINGS | {"newkey": "spam"}),
        ("csv", {"header": "new"}, CSV_DEFAULT_SETTINGS | {"header": "new"}),
        (
            "csv",
            {"pandas_read_csv": {"newkey": "spam"}},
            CSV_DEFAULT_SETTINGS | {"newkey": "spam"},
        ),
        (
            "csv",
            {"pandas_read_csv": {"header": "new"}},
            CSV_DEFAULT_SETTINGS | {"header": "new"},
        ),
        (
            "csv",
            {"header": "b", "pandas_read_csv": {"header": "a"}},
            CSV_DEFAULT_SETTINGS | {"header": "a"},
        ),
        (
            "csv",
            {"header": "b", "pandas_read_csv": None},
            CSV_DEFAULT_SETTINGS | {"header": "b"},
        ),
        # JSON PARSER
        ("json", {}, JSON_DEFAULT_SETTINGS),
        ("json", None, JSON_DEFAULT_SETTINGS),
        ("json", {"newkey": "spam"}, JSON_DEFAULT_SETTINGS | {"newkey": "spam"}),
        ("json", {"header": "new"}, JSON_DEFAULT_SETTINGS | {"header": "new"}),
        (
            # pandas_json_normalize keywords are NOT merged with settings, in contrary
            # to pandas_read_csv with the CSV parser. Instead, the normalisation
            # keywords are stored as attribute within the class (see JsonParser.normalize_kws)
            "json",
            {"pandas_json_normalize": {"newkey": "spam"}},
            JSON_DEFAULT_SETTINGS,
        ),
    ],
)
def test__get_parser__settings(parser_type, settings, expected):
    parser = get_parser(parser_type, settings)
    assert parser.settings == expected
