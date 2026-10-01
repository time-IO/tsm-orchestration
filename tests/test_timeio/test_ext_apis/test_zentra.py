#! /usr/bin/env python
# -*- coding: utf-8 -*-

from .conf import mock_thing, mock_response

from timeio import ext_api


def _readings(count, start_mrid=100):
    """Build `count` fake readings with increasing mrid."""
    return [
        {
            "mrid": start_mrid + i,
            "timestamp_utc": 1700000000 + i * 60,
            "value": 12.3 + i,
        }
        for i in range(count)
    ]


def _api_response(count, start_mrid=100):
    return {
        "data": {
            "Port 1": [
                {
                    "metadata": {
                        "device_name": "test_device",
                        "sensor_name": "temp",
                        "units": "C",
                    },
                    "readings": _readings(count, start_mrid),
                }
            ]
        }
    }


def test_zentra_do_parse():
    api_response = _api_response(count=3, start_mrid=100)
    parsed = ext_api.ZentraApiSyncer().do_parse(api_response)

    assert len(parsed) == 3
    obs = parsed[0]
    assert obs["result_number"] == 12.3
    assert obs["datastream_pos"] == "Port 1"
    assert "zentra_api" in obs["parameters"]
