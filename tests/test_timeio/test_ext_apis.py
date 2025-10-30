#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import base64
import pytest
from unittest.mock import patch, MagicMock, Mock

from timeio import ext_api

CONTENT = {
    "thing": "UUID",
    "datetime_from": "from",
    "datetime_to": "to",
}


@pytest.fixture
def mock_thing():
    class MockThing:
        def __init__(self, settings):
            self.ext_api = type("ExtApi", (), {"settings": settings})

    return MockThing


@pytest.fixture
def mock_response():
    def _response(status_code=200, data=None, text=None):
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = data
        mock.text = text
        mock.raise_for_status.side_effect = (
            None if status_code < 400 else ext_api.requests.HTTPError(response=mock)
        )
        return mock

    return _response


def test_no_https_error(mock_thing):
    settings = {
        "version": 1,
        "endpoint": "http://bosch.test",
        "sensor_id": "sensor",
        "username": "user",
        "password": "enc_pw",
        "period": 1,
    }
    thing = mock_thing(settings)
    syncer = ext_api.BoschApiSyncer()
    with pytest.raises(ext_api.NoHttpsError) as r:
        syncer.fetch_api_data(thing, CONTENT)


def test_bosch_basic_auth():
    token = ext_api.BoschApiSyncer.basic_auth("user", "pw")
    encoded = token.split(" ")[1]
    assert base64.b64decode(encoded).decode() == "user:pw"


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_pw")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_bosch_fetch_api_data(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    mock_request.return_value = mock_response(
        data=[{"payload": {"observations": ["data"]}}]
    )

    settings = {
        "version": 1,
        "endpoint": "https://bosch.test",
        "sensor_id": "sensor",
        "username": "user",
        "password": "enc_pw",
        "period": 1,
    }
    thing = mock_thing(settings)

    data = ext_api.BoschApiSyncer().fetch_api_data(thing, CONTENT)

    assert isinstance(data, list)
    mock_decrypt.assert_called_once_with("enc_pw", "secret_key")
    mock_request.assert_called_once()
    called_url = mock_request.call_args[0][1]
    assert called_url.startswith("https://bosch.test/sensor/")


def test_bosch_do_parse():
    api_response = [
        {
            "payload": {
                "Type": "DATA",
                "UTC": "2025-05-21T09:12:49.000Z",
                "deviceID": "device_id",
                "param1": 1,
                "param2": 2,
                "param3": 3,
            }
        },
        {
            "payload": {
                "Type": "DATA",
                "UTC": "2025-05-21T09:13:49.000Z",
                "deviceID": "device_id",
                "param1": 3,
                "param2": 2,
                "param3": 1,
            }
        },
    ]
    parsed = ext_api.BoschApiSyncer().do_parse(api_response)
    obs = parsed["observations"][0]
    assert len(parsed["observations"]) == 6
    assert obs["result_number"] == 1
    assert "bosch_data" in obs["parameters"]


def test_tsystems_unix_ts_to_str():
    syncer = ext_api.TsystemsApiSyncer()
    ts = 1735689600
    result = syncer.unix_ts_to_str(ts)
    assert result == "2025-01-01 00:00:00"


@patch("timeio.ext_api.request_with_handling")
def test_tsystems_get_bearer_token(mock_request, mock_response):
    mock_request.return_value = mock_response(data={"access_token": "fake_token"})
    syncer = ext_api.TsystemsApiSyncer()
    token = syncer.get_bearer_token("user1", "pass1")
    assert token == "fake_token"
    mock_request.assert_called_once_with(
        "POST",
        syncer.tsytems_auth_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": "lcmm",
            "grant_type": "password",
            "username": "user1",
            "password": "pass1",
        },
    )


@patch("timeio.ext_api.request_with_handling")
def test_tsystems_get_bearer_token_key_error(mock_request, mock_response):
    mock_request.return_value = mock_response(data={})
    syncer = ext_api.TsystemsApiSyncer()

    with pytest.raises(KeyError):
        syncer.get_bearer_token("user1", "pass1")


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_pw")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_tsystems_fetch_api_data(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    settings = {
        "group": "group",
        "version": 1,
        "password": "enc_pw",
        "username": "user",
        "station_id": "uuid",
    }
    thing = mock_thing(settings)
    syncer = ext_api.TsystemsApiSyncer()
    syncer.get_bearer_token = MagicMock(return_value="bearer_token")
    mock_request.return_value = mock_response(data=[{"data": "ok"}])
    data = syncer.fetch_api_data(thing, CONTENT)

    assert data == [{"data": "ok"}]
    mock_decrypt.assert_called_once_with("enc_pw", "secret_key")
    syncer.get_bearer_token.assert_called_once_with("user", "dec_pw")
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer bearer_token"
    assert kwargs["params"]["aggregationTime"] == "FINEST"


def test_tsytsems_do_parse():
    api_response = [
        {
            "deviceId": "device_id",
            "locationId": "location_id",
            "timestamp": 1730548000,
            "param1": 1,
            "param2": 2,
        },
        {
            "deviceId": "device_id",
            "locationId": "location_id",
            "timestamp": 1730448000,
            "param1": 3,
            "param2": 2,
        },
    ]
    parsed = ext_api.TsystemsApiSyncer().do_parse(api_response)
    obs = parsed["observations"][0]
    assert len(parsed["observations"]) == 4
    assert obs["result_number"] == 1
    assert (
        obs["parameters"]
        == '{"origin": "tsystems_data", "column_header": {"sensor_id": "device_id", "location_id": "location_id", "aggregation_time": "hourly"}}'
    )


@patch("timeio.ext_api.request_with_handling")
def test_dwd_fetch_api_data(mock_request, mock_response, mock_thing):
    mock_request.return_value = mock_response(data={"weather": []})
    settings = {"station_id": "station_id"}
    thing = mock_thing(settings)
    result = ext_api.DwdApiSyncer().fetch_api_data(thing, CONTENT)
    mock_request.assert_called_once()
    called_args, called_kwargs = mock_request.call_args
    assert called_args[0] == "GET"
    assert called_args[1] == ext_api.DwdApiSyncer.brightsky_base_url
    assert called_kwargs["params"]["dwd_station_id"] == "station_id"
    assert result == {"weather": []}


def test_dwd_do_parse():
    api_response = {
        "weather": [
            {
                "timestamp": "2025-01-01T00:00:00Z",
                "temperature": 5.1,
                "condition": "rain",
                "fallback_source_ids": None,
                "source_id": 123,
            },
            {
                "timestamp": "2025-01-01T01:00:00Z",
                "temperature": None,
                "condition": "rain",
                "source_id": 123,
            },
        ],
        "sources": [
            {
                "id": 1,
                "dwd_station_id": "station_id",
                "lat": 51.0,
                "lon": 11.0,
            }
        ],
    }
    syncer = ext_api.DwdApiSyncer()
    parsed = syncer.do_parse(api_response)
    obs = parsed["observations"][1]
    assert len(parsed["observations"]) == 3
    assert obs["result_string"] == "rain"
    assert "dwd_data" in obs["parameters"]


@pytest.mark.parametrize(
    "value, expected", [(1, 0), (1.1, 0), ("string", 1), ({"key": "val"}, 2), (True, 3)]
)
def test_ttn_dynamic_parameter_mapping(value, expected):
    assert ext_api.TtnApiSyncer.dynamic_parameter_mapping(value) == expected


def test_ttn_dynamic_parameter_mapping_invalid():
    with pytest.raises(ext_api.ExtApiRequestError):
        ext_api.TtnApiSyncer.dynamic_parameter_mapping([1, 2])


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_api_key")
@patch("timeio.ext_api.get_crypt_key", return_value="secret")
@patch("timeio.ext_api.json.loads", side_effect=json.loads)
def test_ttn_fetch_api_data(
    mock_json_loads, mock_get_key, mock_decrypt, mock_request, mock_thing, mock_response
):
    raw_json = "\n".join(
        [
            json.dumps(
                {
                    "result": {
                        "uplink_message": {
                            "received_at": "2025-01-01T00:00:00.000000000Z",
                            "decoded_payload": {
                                "param1": 1.1,
                                "param2": "result",
                            },
                        }
                    }
                }
            )
        ]
    )

    mock_request.return_value = mock_response(text=raw_json)
    settings = {"endpoint_uri": "endpoint_uri", "api_key": "enc_api_key"}
    thing = mock_thing(settings)
    data = ext_api.TtnApiSyncer().fetch_api_data(thing, CONTENT)
    mock_decrypt.assert_called_once_with("enc_api_key", "secret")
    mock_request.assert_called_once()
    mock_request.assert_called_once_with(
        "GET",
        "endpoint_uri",
        headers={"Authorization": "Bearer dec_api_key", "Accept": "text/event-stream"},
    )
    assert "response" in data
    assert isinstance(data["response"], list)
    assert data["url"] == "endpoint_uri"


def test_ttn_do_parse():
    api_response = {
        "response": [
            {
                "result": {
                    "uplink_message": {
                        "received_at": "2025-01-01T00:00:00.000000000Z",
                        "decoded_payload": {
                            "param1": 1.1,
                            "param2": "result",
                        },
                    }
                }
            },
            {
                "result": {
                    "uplink_message": {
                        "received_at": "2025-01-01T01:00:00.000000000Z",
                        "decoded_payload": {
                            "param1": 1,
                            "param2": "result",
                        },
                    }
                }
            },
        ],
        "url": "https://api.ttn.test",
    }
    parsed = ext_api.TtnApiSyncer().do_parse(api_response)
    assert len(parsed["observations"]) == 4
    obs = parsed["observations"][0]
    assert json.loads(obs["parameters"])["origin"] == api_response["url"]
    assert "result_number" in obs


def test_ttn_cleanup_json():
    raw = '{"a":1}\n{"b":2}\n'
    expected = '[{"a":1},{"b":2}]'
    result = ext_api.TtnApiSyncer.cleanup_json(raw)
    assert result == expected


def test_ttn_cleanup_json_skips_empty_lines():
    raw = '\n{"a":1}\n\n{"b":2}\n'
    expected = '[{"a":1},{"b":2}]'
    result = ext_api.TtnApiSyncer.cleanup_json(raw)
    assert result == expected


def test_ttn_cleanup_json_empty_input():
    result = ext_api.TtnApiSyncer.cleanup_json("")
    assert result == "[]"
