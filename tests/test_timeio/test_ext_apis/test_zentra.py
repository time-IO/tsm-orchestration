#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from unittest.mock import patch, MagicMock
from .conf import CONTENT, mock_thing, mock_response

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


ZENTRA_SETTINGS = {
    "device_sn": "z6-00930",
    "api_key": "enc_key",
    "period_in_minutes": 15,
    "units": "metric",
    "last_mrid": None,
}


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_key")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_zentra_fetch_uses_dates_when_no_checkpoint(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    mock_request.return_value = mock_response(data=_api_response(count=5))

    thing = mock_thing(ZENTRA_SETTINGS)
    thing.ext_api.update_last_mrid = MagicMock()

    syncer = ext_api.ZentraApiSyncer()
    syncer.fetch_api_data(thing, CONTENT)

    called_params = mock_request.call_args.kwargs["params"]
    assert called_params["start_date"] == CONTENT["datetime_from"]
    assert called_params["end_date"] == CONTENT["datetime_to"]
    assert "start_mrid" not in called_params
    mock_decrypt.assert_called_once_with("enc_key", "secret_key")


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_key")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_zentra_fetch_uses_mrid_when_checkpoint_set(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    mock_request.return_value = mock_response(data=_api_response(count=5))

    settings = {**ZENTRA_SETTINGS, "last_mrid": "500"}
    thing = mock_thing(settings)
    thing.ext_api.update_last_mrid = MagicMock()

    syncer = ext_api.ZentraApiSyncer()
    syncer.fetch_api_data(thing, CONTENT)

    called_params = mock_request.call_args.kwargs["params"]
    assert called_params["start_mrid"] == "500"
    assert "start_date" not in called_params
    assert "end_date" not in called_params


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_key")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_zentra_checkpoint_saved_when_page_full(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    # per_page reached exactly -> assume more data waiting
    mock_request.return_value = mock_response(
        data=_api_response(count=2000, start_mrid=1000)
    )

    thing = mock_thing(ZENTRA_SETTINGS)
    thing.ext_api.update_last_mrid = MagicMock()

    syncer = ext_api.ZentraApiSyncer()
    syncer.fetch_api_data(thing, CONTENT)

    thing.ext_api.update_last_mrid.assert_called_once_with("2999")


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_key")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_zentra_checkpoint_cleared_when_backlog_caught_up(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    # fewer readings than per_page -> backlog is done
    mock_request.return_value = mock_response(data=_api_response(count=5))

    settings = {**ZENTRA_SETTINGS, "last_mrid": "500"}
    thing = mock_thing(settings)
    thing.ext_api.update_last_mrid = MagicMock()

    syncer = ext_api.ZentraApiSyncer()
    syncer.fetch_api_data(thing, CONTENT)

    thing.ext_api.update_last_mrid.assert_called_once_with(None)


@patch("timeio.ext_api.request_with_handling")
@patch("timeio.ext_api.decrypt", return_value="dec_key")
@patch("timeio.ext_api.get_crypt_key", return_value="secret_key")
def test_zentra_checkpoint_untouched_on_normal_sync(
    mock_get_key, mock_decrypt, mock_request, mock_response, mock_thing
):
    # normal sync, no backlog, page not full -> update_last_mrid never called
    mock_request.return_value = mock_response(data=_api_response(count=5))

    thing = mock_thing(ZENTRA_SETTINGS)
    thing.ext_api.update_last_mrid = MagicMock()

    syncer = ext_api.ZentraApiSyncer()
    syncer.fetch_api_data(thing, CONTENT)

    thing.ext_api.update_last_mrid.assert_not_called()


def test_zentra_do_parse():
    api_response = _api_response(count=3, start_mrid=100)
    parsed = ext_api.ZentraApiSyncer().do_parse(api_response)

    assert len(parsed) == 3
    obs = parsed[0]
    assert obs["result_number"] == 12.3
    assert obs["datastream_pos"] == "Port 1"
    assert "zentra_api" in obs["parameters"]