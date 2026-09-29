#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from unittest.mock import patch
from .conf import CONTENT, mock_thing, mock_response

from timeio import ext_api

SENSOTO_SETTINGS = {
    "network": "net1",
    "device": "dev1",
    "period_in_minutes": 15,
}


@patch("timeio.ext_api.request_with_handling")
def test_sensoto_fetch_api_data(mock_request, mock_response, mock_thing):
    thing = mock_thing(SENSOTO_SETTINGS)

    sensors_response = mock_response(data={"items": [{"name": "s1"}, {"name": "s2"}]})
    agg_s1 = mock_response(data={"phenomenon": {"aggregation": "avg"}})
    agg_s2 = mock_response(data={"phenomenon": {"aggregation": "sum"}})
    measurements_s1 = mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 1.1}])
    measurements_s2 = mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 2.2}])

    mock_request.side_effect = [
        sensors_response,
        agg_s1,
        agg_s2,
        measurements_s1,
        measurements_s2,
    ]

    data = ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    assert mock_request.call_count == 5
    assert len(data) == 2
    assert data[0]["sensor"] == "s1"
    assert data[0]["network"] == "net1"
    assert data[0]["device"] == "dev1"
    assert data[0]["v"] == 1.1
    assert data[1]["sensor"] == "s2"
    assert data[1]["v"] == 2.2

    # verify measurement requests used the correct time window and params
    last_call = mock_request.call_args_list[-1]
    assert last_call.kwargs["params"]["start"] == CONTENT["datetime_from"]
    assert last_call.kwargs["params"]["end"] == CONTENT["datetime_to"]


@patch("timeio.ext_api.request_with_handling")
def test_sensoto_get_sensor_data(mock_request, mock_response, mock_thing):
    sensors_response = mock_response(data={"items": [{"name": "s1"}]})
    agg_s1 = mock_response(data={"phenomenon": {"aggregation": "avg"}})
    mock_request.side_effect = [sensors_response, agg_s1]

    result = ext_api.SensotoApiSyncer().get_sensor_data("net1", "dev1")

    assert result == [{"sensor": "s1", "aggregation": "avg"}]


def test_sensoto_do_parse():
    api_response = [
        {
            "network": "net1",
            "device": "dev1",
            "sensor": "s1",
            "end": "2025-01-01T00:15Z",
            "v": 1.1,
        },
        {
            "network": "net1",
            "device": "dev1",
            "sensor": "s2",
            "end": "2025-01-01T00:15Z",
            "v": 2.2,
        },
    ]
    parsed = ext_api.SensotoApiSyncer().do_parse(api_response)

    assert len(parsed) == 2
    obs = parsed[0]
    assert obs["result_number"] == 1.1
    assert obs["datastream_pos"] == "s1"
    assert obs["result_time"] == "2025-01-01T00:15Z"
    assert "sensoto_data" in obs["parameters"]
