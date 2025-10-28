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
    else:
        assert not hasattr(parser, "settings")
