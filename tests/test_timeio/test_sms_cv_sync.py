#!/usr/bin/env python3

import pytest

from timeio.sms import SmsCVSyncer
from time import strptime


@pytest.fixture()
def patch():
    pass


def test__SmsCvSyncer_get_utc_str():
    now = SmsCVSyncer.get_utc_str()
    assert isinstance(now, str)
    assert strptime(now, "%Y-%m-%d %H:%M:%S (UTC)")


@pytest.mark.parametrize(
    "data, expected",
    [
        ([], []),
        ([{"id": 1}], [{"id": 1}]),
        ([{"id": 1}, {"id": 1}], [{"id": 1}]),
        ([{"id": 1}, {"id": 2}, {"id": 2}, {"id": 1}], [{"id": 1}, {"id": 2}]),
    ],
)
def test__SmsCvSyncer_remove_id_duplicates(data, expected):
    result = SmsCVSyncer._remove_id_duplicates(data)
    assert result == expected


def test__SmsCvSyncer_remove_id_duplicates__raise_KeyError():
    with pytest.raises(KeyError, match="id"):
        SmsCVSyncer._remove_id_duplicates([{}])


@pytest.mark.parametrize(
    "data, path, expected",
    [
        ({"a": 99}, ["a"], 99),
        ({"a": {"a": 99}}, ["a", "a"], 99),
        ({"a": {"a": 11, "b": 12}, "b": {"a": 21, "b": 22}}, ["a", "a"], 11),
        ({"a": {"a": 11, "b": 12}, "b": {"a": 21, "b": 22}}, ["a", "b"], 12),
        ({"a": {"a": 11, "b": 12}, "b": {"a": 21, "b": 22}}, ["b", "a"], 21),
        ({"a": {"a": 11, "b": 12}, "b": {"a": 21, "b": 22}}, ["b", "b"], 22),
    ],
)
def test__SmsCvSyncer_value_from_dict(data, path, expected):
    result = SmsCVSyncer._value_from_dict(data, path)
    assert result == expected


def test__SmsCvSyncer_value_from_dict__raise_KeyError():
    with pytest.raises(KeyError, match="missing"):
        SmsCVSyncer._value_from_dict({"a": 99}, ["missing"])


def test__SmsCvSyncer_to_postgres_str__warns_deprecated():
    with pytest.deprecated_call():
        SmsCVSyncer._to_postgres_str("foo")


@pytest.mark.filterwarnings("ignore:Deprecated method")
@pytest.mark.parametrize(
    "val, expected",
    [
        (None, "NULL"),
        (True, "True"),
        (False, "False"),
        (0, "0"),
        (42, "42"),
        (0.0, "0.0"),
        (0.000, "0.0"),
        (0.0001, "0.0001"),
        (42.3, "42.3"),
        ("42", "42"),  # string ints are converted to ints
        ("foo", "'foo'"),
        ("42.", "'42.'"),  # string floats are converted to strings
        ("42.0001", "'42.0001'"),  # string floats are converted to strings
    ],
)
def test__SmsCvSyncer_to_postgres_str(val, expected):
    result = SmsCVSyncer._to_postgres_str(val)
    assert result == expected


@pytest.mark.filterwarnings("ignore:Deprecated method")
def test__SmsCvSyncer_to_postgres_str__raises_TypeError():
    with pytest.raises(TypeError, match="Unconvertible type .*"):
        SmsCVSyncer._to_postgres_str([])  # type: ignore


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            {"name": "empty_table", "keys": {}},
            'CREATE TABLE IF NOT EXISTS "empty_table" ()',
        ),
        (
            {
                "name": "a_table",
                "keys": {
                    "a": {"type": "BIGINT"},
                    "b": {"type": "VARCHAR(200)", "other": "ignored"},
                },
            },
            'CREATE TABLE IF NOT EXISTS "a_table" ("a" BIGINT, "b" VARCHAR(200))',
        ),
    ],
)
def test__SmsCvSyncer_table_create_query(data, expected):
    result = SmsCVSyncer._table_create_query(data)
    assert result.as_string() == expected


@pytest.mark.parametrize(
    "table_dict, data, expected",
    [
        (
            {  # table dict
                "name": "some_table",
                "keys": {
                    "id": {"path": ["id"]},
                    "term": {"path": ["attributes", "term"]},
                },
            },
            [  # data
                {"id": 1, "attributes": {"term": "abc"}},
                {"id": 2, "attributes": {"term": "xyz"}},
            ],
            # expected
            'INSERT INTO "some_table" ("id", "term") VALUES '
            "(1, 'abc'), (2, 'xyz') "
            "ON CONFLICT (id) DO UPDATE SET "
            '"term" = EXCLUDED."term"',
        ),
        (
            {  # table dict
                "name": "TestValuesTable",
                "keys": {
                    "val1": {"path": ["v1"]},
                    "val2": {"path": ["v2"]},
                    "val3": {"path": ["v3"]},
                },
            },
            [  # data
                {"v1": None, "v2": True, "v3": False},
                {"v1": 0, "v2": 42, "v3": 0.0},
                {"v1": 0.000, "v2": 0.0001, "v3": 42.3},
                {"v1": "a_string", "v2": "with space", "v3": ""},
                {"v1": 'double "quotes"', "v2": "single 'quotes'", "v3": "a' quote"},
                {"v1": "42", "v2": "42.", "v3": "42.001"},
            ],
            'INSERT INTO "TestValuesTable" ("val1", "val2", "val3") VALUES '
            "(NULL, true, false), "
            "(0, 42, 0.0), "
            "(0.0, 0.0001, 42.3), "
            "('a_string', 'with space', ''), "
            """('double "quotes"', 'single ''quotes''', 'a'' quote'), """
            "(42, '42.', '42.001') "
            "ON CONFLICT (id) DO UPDATE SET "
            '"val1" = EXCLUDED."val1", '
            '"val2" = EXCLUDED."val2", '
            '"val3" = EXCLUDED."val3"',
        ),
    ],
)
def test__SmsCvSyncer_table_upsert_query(table_dict, data, expected):
    self = SmsCVSyncer
    result = SmsCVSyncer._table_upsert_query(self, table_dict, data)
    assert result.as_string() == expected
