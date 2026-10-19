import json
import pytest
from unittest.mock import MagicMock, patch
from paho.mqtt.client import MQTTMessage
from run_mqtt_ingest import ParseMqttDataHandler
from timeio.errors import ProcessingError, UserInputError


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("TOPIC", "test/topic")
    monkeypatch.setenv("MQTT_BROKER", "broker:1883")
    monkeypatch.setenv("MQTT_USER", "user")
    monkeypatch.setenv("MQTT_PASSWORD", "pw")
    monkeypatch.setenv("MQTT_CLIENT_ID", "cid")
    monkeypatch.setenv("MQTT_QOS", "1")
    monkeypatch.setenv("MQTT_CLEAN_SESSION", "true")
    monkeypatch.setenv("DSMDB_DSN", "dsn")
    monkeypatch.setenv("DB_API_BASE_URL", "http://fake-db")
    monkeypatch.setenv("DB_API_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOPIC_DATA_PARSED", "topic/parsed")


@patch("run_mqtt_ingest.DBapi")
@patch("run_mqtt_ingest.Thing")
@patch("run_mqtt_ingest.get_parser")
def test_act_parses_and_publishes(mock_get_parser, mock_Thing, mock_DBapi, mock_env):
    handler = ParseMqttDataHandler()
    msg = MQTTMessage(topic=b"user/topic")
    msg.payload = b"{}"

    mock_thing = MagicMock()
    mock_thing.uuid = "UUID"
    mock_thing.mqtt.mqtt_device_type.name = "campbell_cr6"
    mock_Thing.from_mqtt_user_name.return_value = mock_thing

    parser_instance = MagicMock()
    parser_instance.do_parse.return_value = ["parsed"]
    parser_instance.to_observations.return_value = [{"result_number": 1}]
    parser_instance.start_date = "2025-01-01T00:00:00+00:00"
    parser_instance.end_date = "2025-01-01T01:00:00+00:00"
    mock_get_parser.return_value = parser_instance

    handler.dbapi.upsert_observations = MagicMock()
    handler.mqtt_client = MagicMock()

    handler.act({}, msg)

    handler.dbapi.upsert_observations_and_datastreams.assert_called_once_with(
        "UUID", [{"result_number": 1}], mutable=False
    )
    handler.mqtt_client.publish.assert_called_once()
    args, kwargs = handler.mqtt_client.publish.call_args
    assert handler.pub_topic in kwargs["topic"] or args[0] == handler.pub_topic
    payload = json.loads(kwargs.get("payload") or args[1])
    assert payload["thing_uuid"] == "UUID"


@patch("run_mqtt_ingest.journal")
@patch("run_mqtt_ingest.DBapi")
@patch("run_mqtt_ingest.Thing")
@patch("run_mqtt_ingest.get_parser")
def test_act_store_failure_raises_and_does_not_publish(
    mock_get_parser, mock_Thing, mock_DBapi, mock_journal, mock_env
):
    handler = ParseMqttDataHandler()
    msg = MQTTMessage(topic=b"user/topic")
    msg.payload = b"{}"

    mock_thing = MagicMock()
    mock_thing.uuid = "UUID"
    mock_Thing.from_mqtt_user_name.return_value = mock_thing
    mock_get_parser.return_value = MagicMock()

    handler.dbapi.upsert_observations_and_datastreams.side_effect = RuntimeError(
        "db api down"
    )
    handler.mqtt_client = MagicMock()

    with pytest.raises(ProcessingError):
        handler.act({}, msg)

    handler.mqtt_client.publish.assert_not_called()
    mock_journal.error.assert_called_once()
    mock_journal.info.assert_not_called()


def _handler_with_thing(mock_Thing, mock_get_parser, parser):
    handler = ParseMqttDataHandler()
    mock_Thing.from_mqtt_user_name.return_value = MagicMock(uuid="UUID")
    mock_get_parser.return_value = parser
    handler.mqtt_client = MagicMock()
    msg = MQTTMessage(topic=b"mqtt_ingest/user/topic")
    return handler, msg


@patch("run_mqtt_ingest.journal")
@patch("run_mqtt_ingest.DBapi")
@patch("run_mqtt_ingest.Thing")
@patch("run_mqtt_ingest.get_parser")
def test_act_journals_observation_count(
    mock_get_parser, mock_Thing, mock_DBapi, mock_journal, mock_env
):
    parser = MagicMock(start_date=None, end_date=None)
    parser.to_observations.return_value = [{"a": 1}, {"a": 2}, {"a": 3}]
    handler, msg = _handler_with_thing(mock_Thing, mock_get_parser, parser)

    handler.act({}, msg)

    mock_journal.info.assert_called_once()
    assert "stored observations: 3" in mock_journal.info.call_args.args[0]
    mock_journal.warning.assert_not_called()
    mock_journal.error.assert_not_called()


@patch("run_mqtt_ingest.journal")
@patch("run_mqtt_ingest.DBapi")
@patch("run_mqtt_ingest.Thing")
@patch("run_mqtt_ingest.get_parser")
def test_act_journals_warning_without_observations(
    mock_get_parser, mock_Thing, mock_DBapi, mock_journal, mock_env
):
    parser = MagicMock(start_date=None, end_date=None)
    parser.to_observations.return_value = []
    handler, msg = _handler_with_thing(mock_Thing, mock_get_parser, parser)

    handler.act({}, msg)

    mock_journal.warning.assert_called_once()
    assert "no observations" in mock_journal.warning.call_args.args[0]
    mock_journal.info.assert_not_called()
    mock_journal.error.assert_not_called()
    handler.dbapi.upsert_observations_and_datastreams.assert_not_called()
    handler.mqtt_client.publish.assert_not_called()


@patch("run_mqtt_ingest.journal")
@patch("run_mqtt_ingest.DBapi")
@patch("run_mqtt_ingest.Thing")
@patch("run_mqtt_ingest.get_parser")
def test_act_journals_parsing_error_detail(
    mock_get_parser, mock_Thing, mock_DBapi, mock_journal, mock_env
):
    parser = MagicMock()
    parser.do_parse.side_effect = KeyError("time")
    handler, msg = _handler_with_thing(mock_Thing, mock_get_parser, parser)

    with pytest.raises(UserInputError):
        handler.act({}, msg)

    mock_journal.error.assert_called_once()
    text = mock_journal.error.call_args.args[0]
    assert text == "Parsing failed: missing key 'time'"
    mock_journal.info.assert_not_called()


@patch("run_mqtt_ingest.journal")
@patch("run_mqtt_ingest.DBapi")
@patch("run_mqtt_ingest.Thing")
@patch("run_mqtt_ingest.get_parser")
def test_act_journals_unknown_device_type(
    mock_get_parser, mock_Thing, mock_DBapi, mock_journal, mock_env
):
    handler, msg = _handler_with_thing(mock_Thing, mock_get_parser, MagicMock())
    mock_Thing.from_mqtt_user_name.return_value.mqtt.mqtt_device_type.name = "foo"
    mock_get_parser.side_effect = NotImplementedError("parser 'foo' not known")

    with pytest.raises(NotImplementedError):
        handler.act({}, msg)

    assert "'foo'" in mock_journal.error.call_args.args[0]
