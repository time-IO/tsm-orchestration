#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
from unittest.mock import patch

from .conf import CONTENT, mock_thing, mock_response

from timeio import ext_api

SETTINGS = {
    "customer_id": 479,
    "serial_number": "22935",
    "api_key": "enc_key",
    "period_in_minutes": 60,
}

# trimmed real records from device 22935
RECORDS = [
    {
        "avrg": 60,
        "timestamp": "2026-04-01T00:00:35+00:00",
        "saved_at": "2026-04-01T00:01:22.844469+00:00",
        "pm2_5": 4.024056434631348,
        "weather_t": 5.739999771118164,
    },
    {
        "avrg": 60,
        "timestamp": "2026-04-01T00:01:35+00:00",
        "saved_at": "2026-04-01T00:02:24.793414+00:00",
        "pm2_5": 4.05015754699707,
        "weather_t": None,
    },
    {
        "avrg": 60,
        "timestamp": "2026-08-25T10:34:22.598+00:00",
        "saved_at": "2026-08-25T10:35:01.1+00:00",
        "pm2_5": 3.856369972229004,
        "weather_t": 5.730000019073486,
    },
]


def _page(mock_response, records, total=None):
    res = mock_response(data=[dict(r) for r in records])
    res.headers = {} if total is None else {"Total-Count": str(total)}
    return res


def test_myatmosphere_do_parse():
    records = [dict(r, serial_number="22935") for r in RECORDS]
    parsed = ext_api.MyAtmosphereApiSyncer().do_parse(records)

    # 3 records x (avrg, pm2_5, weather_t) minus one None
    assert len(parsed) == 8
    assert {p["datastream_pos"] for p in parsed} == {"avrg", "pm2_5", "weather_t"}
    obs = next(p for p in parsed if p["datastream_pos"] == "pm2_5")
    assert obs["result_time"] == "2026-04-01T00:00:35+00:00"
    assert obs["result_type"] == 0
    assert obs["result_number"] == 4.024056434631348
    assert json.loads(obs["parameters"]) == {
        "origin": "myatmosphere_api",
        "column_header": {"serial_number": "22935"},
    }


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_key")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_myatmosphere_fetch_pages_by_total_count(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    syncer = ext_api.MyAtmosphereApiSyncer()
    syncer.page_size = 2
    mock_request.side_effect = [
        _page(mock_response, RECORDS[:2], total=3),
        _page(mock_response, RECORDS[2:], total=3),
    ]
    data = syncer.fetch_api_data(mock_thing(SETTINGS), CONTENT)

    assert [r["timestamp"] for r in data] == [r["timestamp"] for r in RECORDS]
    assert all(r["serial_number"] == "22935" for r in data)
    mock_decrypt.assert_called_once_with("enc_key", "secret_key")
    assert mock_request.call_count == 2
    first, second = mock_request.call_args_list
    assert first.args[1] == (
        "https://api.my-atmosphere.cloud/api/customers/479/devices/22935/measurements"
    )
    assert first.kwargs["headers"] == {"Api-Key": "dec_key"}
    params = first.kwargs["params"]
    assert params["$filter"] == (
        "timestamp ge 2025-01-01T00:00:00Z and timestamp lt 2025-01-01T01:00:00Z"
    )
    assert params["$orderby"] == "timestamp asc"
    assert params["$top"] == 2
    assert params["$skip"] == 0
    assert second.kwargs["params"]["$skip"] == 2


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_key")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_myatmosphere_fetch_without_total_count_stops_on_short_page(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    syncer = ext_api.MyAtmosphereApiSyncer()
    syncer.page_size = 2
    mock_request.side_effect = [
        _page(mock_response, RECORDS[:2]),
        _page(mock_response, RECORDS[2:]),
    ]
    data = syncer.fetch_api_data(mock_thing(SETTINGS), CONTENT)

    assert len(data) == 3
    assert mock_request.call_count == 2


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_key")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_myatmosphere_fetch_empty_window(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    mock_request.return_value = _page(mock_response, [], total=0)
    data = ext_api.MyAtmosphereApiSyncer().fetch_api_data(mock_thing(SETTINGS), CONTENT)

    assert data == []
    assert mock_request.call_count == 1
