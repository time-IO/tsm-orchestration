import json
from unittest.mock import MagicMock, patch

import pytest
from paho.mqtt.client import MQTTMessage

from sync_extapi_manager import SyncExtApiManager


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("TOPIC", "sync_ext_apis")
    monkeypatch.setenv("MQTT_BROKER", "broker:1883")
    monkeypatch.setenv("MQTT_USER", "user")
    monkeypatch.setenv("MQTT_PASSWORD", "pw")
    monkeypatch.setenv("MQTT_CLIENT_ID", "cid")
    monkeypatch.setenv("MQTT_QOS", "1")
    monkeypatch.setenv("MQTT_CLEAN_SESSION", "true")
    monkeypatch.setenv("DSMDB_DSN", "dsn")
    monkeypatch.setenv("DB_API_BASE_URL", "http://fake-db")
    monkeypatch.setenv("DB_API_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOPIC_DATA_PARSED", "custom/data_parsed")


@patch("sync_extapi_manager.DBapi")
@patch("sync_extapi_manager.Thing")
def test_act_publishes_to_configured_data_parsed_topic(
    mock_Thing, mock_DBapi, mock_env
):
    handler = SyncExtApiManager()
    thing = MagicMock(uuid="UUID")
    thing.name = "thing"
    thing.ext_api.api_type_name = "dwd"
    mock_Thing.from_uuid.return_value = thing
    syncer = MagicMock()
    syncer.do_parse.return_value = [{"result_number": 1}]
    handler.sync_handlers["dwd"] = syncer
    handler.dbapi = MagicMock()
    handler.mqtt_client = MagicMock()
    content = {
        "thing": "UUID",
        "datetime_from": "2025-01-01T00:00:00",
        "datetime_to": "2025-01-02T00:00:00",
    }

    handler.act(content, MQTTMessage(topic=b"sync_ext_apis"))

    handler.dbapi.upsert_observations_and_datastreams.assert_called_once_with(
        "UUID", [{"result_number": 1}], mutable=False
    )
    kwargs = handler.mqtt_client.publish.call_args.kwargs
    assert kwargs["topic"] == "custom/data_parsed"
    assert json.loads(kwargs["payload"]) == {
        "thing_uuid": "UUID",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-01-02T00:00:00",
    }


@patch("sync_extapi_manager.DBapi")
def test_missing_topic_setting_fails_at_startup(mock_DBapi, mock_env, monkeypatch):
    monkeypatch.delenv("TOPIC_DATA_PARSED")
    with pytest.raises(EnvironmentError, match="TOPIC_DATA_PARSED"):
        SyncExtApiManager()
