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


@patch("timeio.ext_api.get_crypt_key", return_value="dummy-key")
@patch("timeio.ext_api.decrypt", return_value="secret-token")
@patch("timeio.ext_api.request_with_handling")
def test_sensoto_fetch_with_token(
    mock_request, mock_decrypt, mock_key, mock_response, mock_thing
):
    thing = mock_thing({**SENSOTO_SETTINGS, "token": "encrypted-token"})
    mock_request.side_effect = [
        mock_response(data={"items": [{"name": "s1"}]}),
        mock_response(data={"phenomenon": {"aggregation": "avg"}}),
        mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 1.1}]),
    ]

    ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    mock_decrypt.assert_called_once_with("encrypted-token", "dummy-key")
    assert mock_request.call_count == 3
    # der Token muss an ALLEN Requests hängen, auch an den beiden in get_sensor_data
    for call in mock_request.call_args_list:
        assert call.kwargs["params"]["token"] == "secret-token"


@pytest.mark.parametrize("token", [None, ""])
@patch("timeio.ext_api.decrypt")
@patch("timeio.ext_api.request_with_handling")
def test_sensoto_fetch_without_token(
    mock_request, mock_decrypt, token, mock_response, mock_thing
):
    thing = mock_thing({**SENSOTO_SETTINGS, "token": token})
    mock_request.side_effect = [
        mock_response(data={"items": [{"name": "s1"}]}),
        mock_response(data={"phenomenon": {"aggregation": "avg"}}),
        mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 1.1}]),
    ]

    ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    mock_decrypt.assert_not_called()
    for call in mock_request.call_args_list:
        assert "token" not in (call.kwargs.get("params") or {})


@pytest.mark.parametrize(
    "organization, expected",
    [
        (None, "open"),
        ("", "open"),
        ("valigruen", "valigruen"),
    ],
)
@patch("timeio.ext_api.request_with_handling")
def test_sensoto_organization_in_url(
    mock_request, organization, expected, mock_response, mock_thing
):
    thing = mock_thing({**SENSOTO_SETTINGS, "organization": organization})
    mock_request.side_effect = [
        mock_response(data={"items": [{"name": "s1"}]}),
        mock_response(data={"phenomenon": {"aggregation": "avg"}}),
        mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 1.1}]),
    ]

    ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    assert mock_request.call_count == 3
    for call in mock_request.call_args_list:
        assert f"/organizations/{expected}/networks/" in call.args[1]


@patch("timeio.ext_api.requests.request")
def test_request_with_handling_masks_token(mock_req):
    import requests
    mock_req.side_effect = requests.exceptions.ConnectionError(
        "Max retries exceeded with url: /x?token=tk1.secret&start=1"
    )
    with pytest.raises(ext_api.ExtApiRequestError) as exc:
        ext_api.request_with_handling("GET", "https://example.org/x")
    assert "tk1.secret" not in str(exc.value)
    assert "token=***" in str(exc.value)


@pytest.mark.parametrize("bad", ["", ".", ".."])
def test_sensoto_seg_rejects_invalid(bad):
    with pytest.raises(ext_api.ExtApiRequestError):
        ext_api.SensotoApiSyncer._seg(bad)


@patch("timeio.ext_api.request_with_handling")
def test_sensoto_fetch_quotes_url_segments(mock_request, mock_response, mock_thing):
    thing = mock_thing(
        {
            **SENSOTO_SETTINGS,
            "organization": "org/x",
            "network": "net/../1",
            "device": "dev?1",
        }
    )
    mock_request.side_effect = [
        mock_response(data={"items": [{"name": "s1"}]}),
        mock_response(data={"phenomenon": {"aggregation": "avg"}}),
        mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 1.1}]),
    ]

    data = ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    expected_prefix = (
        "https://api.sensoto.io/v1/organizations/org%2Fx/networks/"
        "net%2F..%2F1/devices/dev%3F1/sensors"
    )
    assert mock_request.call_count == 3
    for call in mock_request.call_args_list:
        url = call.args[1]
        assert url.startswith(expected_prefix)
        assert "?" not in url
        assert "/../" not in url

    assert data[0]["network"] == "net/../1"
    assert data[0]["device"] == "dev?1"
