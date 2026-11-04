#! /usr/bin/env python
# -*- coding: utf-8 -*-


import pytest
from datetime import datetime


from timeio.parser.mqtt_parser import MqttParser, Observation
from timeio.common import ObservationResultType


class MockParser(MqttParser):
    def do_parse(self, rawdata, origin):
        # Simulate parsing logic
        return [
            Observation(
                timestamp=datetime(2025, 1, 1, 0, 0, 0),
                value=42.0,
                origin=origin,
                position=1,
            ),
            Observation(
                timestamp=datetime(2025, 1, 1, 1, 0, 0),
                value="OK",
                origin=origin,
                position=2,
            ),
            Observation(
                timestamp=datetime(2025, 1, 1, 2, 0, 0),
                value=True,
                origin=origin,
                position=3,
            ),
        ]


@pytest.fixture
def parser():
    return MockParser()


def test_do_parse_returns_observations(parser):
    result = parser.do_parse("raw_data", "mqtt://broker/topic")
    assert len(result) == 3
    assert all(isinstance(obs, Observation) for obs in result)


def test_to_observations_converts_types(parser):
    data = parser.do_parse("data", "origin")
    result = parser.to_observations(data, "thing-uuid")

    assert len(result) == 3

    num = result[0]
    assert num["result_number"] == 42.0
    assert num["result_type"] == ObservationResultType.Number

    string = result[1]
    assert string["result_string"] == "OK"
    assert string["result_type"] == ObservationResultType.String

    boolean = result[2]
    assert boolean["result_boolean"] is True
    assert boolean["result_type"] == ObservationResultType.Bool


def test_invalid_value_raises():
    with pytest.raises(ValueError):
        Observation(timestamp=datetime.now(), value=None, origin="x", position=1)


class FixedParser(MqttParser):
    """Returns the observations it was created with."""

    def __init__(self, observations):
        super().__init__()
        self.observations = observations

    def do_parse(self, rawdata, origin):
        return self.observations


def ob(timestamp, value=1.0, position=0):
    return Observation(timestamp=timestamp, value=value, origin="o", position=position)


def test_to_observations_sets_date_range(parser):
    parser.to_observations(parser.do_parse("data", "origin"), "thing-uuid")
    assert parser.start_date == "2025-01-01T00:00:00"
    assert parser.end_date == "2025-01-01T02:00:00"


def test_date_range_is_unordered_min_max():
    p = FixedParser(
        [
            ob("2025-01-02T00:00:00Z"),
            ob("2025-01-01T00:00:00Z"),
            ob("2025-01-03T00:00:00Z"),
        ]
    )
    p.to_observations(p.do_parse(None, "o"), "thing-uuid")
    assert p.start_date == "2025-01-01T00:00:00+00:00"
    assert p.end_date == "2025-01-03T00:00:00+00:00"


def test_date_range_ignores_skipped_observations():
    p = FixedParser([ob(datetime(2025, 1, 1)), ob(datetime(2030, 1, 1), value=[1, 2])])
    result = p.to_observations(p.do_parse(None, "o"), "thing-uuid")
    assert len(result) == 1
    assert p.start_date == p.end_date == "2025-01-01T00:00:00"


@pytest.mark.parametrize(
    "timestamps",
    [
        [],
        ["not a timestamp"],
        [""],
        [datetime(2025, 1, 1), "2025-01-02T00:00:00Z"],  # naive and aware
    ],
    ids=["empty", "unparsable", "empty-string", "naive-and-aware"],
)
def test_date_range_unset_without_usable_timestamps(timestamps):
    p = FixedParser([ob(ts) for ts in timestamps])
    result = p.to_observations(p.do_parse(None, "o"), "thing-uuid")
    assert len(result) == len(timestamps)
    assert p.start_date is None
    assert p.end_date is None
