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
    measurements_s1 = mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 1.1}])
    measurements_s2 = mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 2.2}])

    mock_request.side_effect = [
        sensors_response,
        measurements_s1,
        measurements_s2,
    ]

    data = ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    assert mock_request.call_count == 3
    assert len(data) == 2
    assert data[0]["sensor"] == "s1"
    assert data[0]["network"] == "net1"
    assert data[0]["device"] == "dev1"
    assert data[0]["v"] == 1.1
    assert data[1]["sensor"] == "s2"
    assert data[1]["v"] == 2.2

    # verify measurement requests used the correct time window and params
    last_call = mock_request.call_args_list[-1]
    assert last_call.kwargs["params"]["start"] == "2025-01-01T00:00:00Z"
    assert last_call.kwargs["params"]["end"] == "2025-01-01T01:00:00Z"


@patch("timeio.ext_api.request_with_handling")
def test_sensoto_get_sensors(mock_request, mock_response):
    mock_request.return_value = mock_response(data={"items": [{"name": "s1"}]})

    assert ext_api.SensotoApiSyncer().get_sensors("net1", "dev1") == ["s1"]


@pytest.mark.parametrize(
    "value, expected",
    [
        ("2026-10-19 00:00:00", "2026-10-19T00:00:00Z"),
        ("2026-10-19T00:00:00Z", "2026-10-19T00:00:00Z"),
        ("2026-10-19T02:00:00+02:00", "2026-10-19T00:00:00Z"),
    ],
)
def test_sensoto_iso(value, expected):
    assert ext_api.SensotoApiSyncer._iso(value) == expected


def _error(mock_response, status_code, data=None, text=None):
    resp = mock_response(status_code=status_code, data=data, text=text)
    if data is None:
        resp.json.side_effect = ValueError("no json")
    return resp


@patch("timeio.ext_api.requests.request")
def test_sensoto_partial_failure(mock_req, mock_response, mock_thing):
    thing = mock_thing(SENSOTO_SETTINGS)
    mock_req.side_effect = [
        mock_response(data={"items": [{"name": "s1"}, {"name": "s2"}]}),
        _error(mock_response, 500, {"code": 500, "message": "boom"}),
        mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 2.2}]),
    ]

    with pytest.raises(ext_api.ExtApiPartialResult) as exc:
        ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    assert [d["sensor"] for d in exc.value.data] == ["s2"]
    assert "1 of 2" in exc.value.msg
    assert "'s1'" in exc.value.msg
    assert "boom" in exc.value.msg
    assert "500" in exc.value.msg


@patch("timeio.ext_api.requests.request")
def test_sensoto_all_sensors_fail(mock_req, mock_response, mock_thing):
    thing = mock_thing(SENSOTO_SETTINGS)
    mock_req.side_effect = [
        mock_response(data={"items": [{"name": "s1"}]}),
        _error(mock_response, 500, text="<html>boom</html>"),
    ]

    with pytest.raises(ext_api.ExtApiRequestError) as exc:
        ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    assert not isinstance(exc.value, ext_api.ExtApiPartialResult)
    assert "1 of 1" in exc.value.msg
    assert "html" not in exc.value.msg


@patch("timeio.ext_api.requests.request")
def test_sensoto_sensor_list_fails(mock_req, mock_response, mock_thing):
    thing = mock_thing(SENSOTO_SETTINGS)
    mock_req.return_value = _error(mock_response, 500, {"message": "no such device"})

    with pytest.raises(ext_api.ExtApiRequestError) as exc:
        ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    assert "sensor list" in exc.value.msg
    assert "no such device" in exc.value.msg


@patch("timeio.ext_api.get_crypt_key", return_value="dummy-key")
@patch("timeio.ext_api.decrypt", return_value="tk1.secret")
@patch("timeio.ext_api.requests.request")
def test_sensoto_error_message_masks_token(
    mock_req, mock_decrypt, mock_key, mock_response, mock_thing
):
    thing = mock_thing({**SENSOTO_SETTINGS, "token": "encrypted-token"})
    mock_req.return_value = _error(
        mock_response, 400, {"message": "bad token tk1.secret, url ?token=other"}
    )

    with pytest.raises(ext_api.ExtApiRequestError) as exc:
        ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    assert "tk1.secret" not in exc.value.msg
    assert "token=other" not in exc.value.msg
    assert "bad token ***" in exc.value.msg


@patch("timeio.ext_api.requests.request")
def test_request_with_handling_keeps_body_out_of_message(mock_req, mock_response):
    mock_req.return_value = _error(mock_response, 400, {"message": "secret echo"})

    with pytest.raises(ext_api.ExtApiRequestError) as exc:
        ext_api.request_with_handling("GET", "https://example.org/x")

    assert exc.value.msg == "HTTP request failed. Status code: 400"
    assert exc.value.response is mock_req.return_value


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
        mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 1.1}]),
    ]

    ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    mock_decrypt.assert_called_once_with("encrypted-token", "dummy-key")
    assert mock_request.call_count == 2
    # der Token muss an ALLEN Requests hängen, auch an der Sensorliste
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
        mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 1.1}]),
    ]

    ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    assert mock_request.call_count == 2
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
        mock_response(data=[{"end": "2025-01-01T00:15Z", "v": 1.1}]),
    ]

    data = ext_api.SensotoApiSyncer().fetch_api_data(thing, CONTENT)

    expected_prefix = (
        "https://api.sensoto.io/v1/organizations/org%2Fx/networks/"
        "net%2F..%2F1/devices/dev%3F1/sensors"
    )
    assert mock_request.call_count == 2
    for call in mock_request.call_args_list:
        url = call.args[1]
        assert url.startswith(expected_prefix)
        assert "?" not in url
        assert "/../" not in url

    assert data[0]["network"] == "net/../1"
    assert data[0]["device"] == "dev?1"
