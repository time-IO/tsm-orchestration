import json
from unittest.mock import MagicMock, patch

from paho.mqtt.client import MQTTMessage

from run_mqtt_ingest import ParseMqttDataHandler
from .test_mqtt_ingest import mock_env  # noqa: F401 (fixture)


@patch("run_mqtt_ingest.DBapi")
@patch("run_mqtt_ingest.Thing")
@patch("run_mqtt_ingest.get_parser")
def test_act_without_time_range_does_not_publish(
    mock_get_parser, mock_Thing, mock_DBapi, mock_env
):
    handler = ParseMqttDataHandler()
    msg = MQTTMessage(topic=b"mqtt_ingest/user/topic")
    msg.payload = b"{}"
    mock_Thing.from_mqtt_user_name.return_value = MagicMock(uuid="UUID")
    parser_instance = MagicMock()
    parser_instance.to_observations.return_value = []
    parser_instance.start_date = None
    parser_instance.end_date = None
    mock_get_parser.return_value = parser_instance
    handler.mqtt_client = MagicMock()
    handler.act({}, msg)

    handler.mqtt_client.publish.assert_not_called()


CAMPBELL_PAYLOAD = {
    "properties": {
        "loggerID": "CR6_18341",
        "observationNames": ["Batt_volt_Min", "PTemp"],
        "observations": {
            "2022-05-24T08:53:00Z": [11.9, 26.91],
            "2022-05-24T08:54:00Z": [11.8, 26.95],
        },
    }
}


@patch("run_mqtt_ingest.DBapi")
@patch("run_mqtt_ingest.Thing")
def test_published_data_parsed_is_accepted_by_qc(mock_Thing, mock_DBapi, mock_env):
    """Real device parser -> data_parsed message -> QC worker message checks."""
    import pandas as pd
    import run_qc
    from timeio.qc.io import read_stream_data

    handler = ParseMqttDataHandler()
    msg = MQTTMessage(topic=b"mqtt_ingest/user/logger")
    thing = MagicMock(uuid="UUID")
    thing.mqtt.mqtt_device_type.name = "campbell_cr6"
    mock_Thing.from_mqtt_user_name.return_value = thing
    handler.mqtt_client = MagicMock()

    handler.act(CAMPBELL_PAYLOAD, msg)

    payload = json.loads(handler.mqtt_client.publish.call_args.kwargs["payload"])
    assert payload == {
        "thing_uuid": "UUID",
        "start_date": "2022-05-24T08:53:00+00:00",
        "end_date": "2022-05-24T08:54:00+00:00",
    }

    # the QC worker validates the message like this (QcHandler._parse_message)
    payload.setdefault("version", 1)
    with patch.object(run_qc.feta.Thing, "from_uuid") as from_uuid:
        project, configs, qc_thing = run_qc.QcHandler._parse_message_v1(None, payload)
    from_uuid.assert_called_once_with("UUID", dsn=None)
    assert qc_thing is from_uuid.return_value

    # ... and turns the dates into the read window
    start, end = pd.Timestamp(payload["start_date"]), pd.Timestamp(payload["end_date"])
    assert start <= end
    assert read_stream_data(MagicMock(), [], start, end) == {}
