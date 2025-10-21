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


def test__SmsCvSyncer_to_postgres_str__raises_TypeError():
    with pytest.raises(TypeError, match="Unconvertible type .*"):
        SmsCVSyncer._to_postgres_str([])  # type: ignore


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            {"name": "empty_table", "keys": {}},
            "CREATE TABLE IF NOT EXISTS empty_table ()",
        ),
        (
            {
                "name": "a_table",
                "keys": {
                    "a": {"type": "BIGINT"},
                    "b": {"type": "VARCHAR(200)", "other": "ignored"},
                },
            },
            "CREATE TABLE IF NOT EXISTS a_table (a BIGINT, b VARCHAR(200))",
        ),
    ],
)
def test__SmsCvSyncer_table_create_query(data, expected):
    result = SmsCVSyncer._table_create_query(data)
    assert result == expected
