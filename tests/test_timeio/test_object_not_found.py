#!/usr/bin/env python3

import json
from unittest.mock import MagicMock, patch

import pytest
from paho.mqtt.client import MQTTMessage

from timeio.errors import DataNotFoundError
from timeio.feta import ObjectNotFound
from run_file_ingest import ParserJobHandler


def test_object_not_found_is_a_data_not_found_error():
    assert issubclass(ObjectNotFound, DataNotFoundError)
    with pytest.raises(ObjectNotFound):  # existing `except ObjectNotFound` still works
        raise ObjectNotFound("x")


@pytest.fixture
def file_ingest_env(monkeypatch):
    for k, v in {
        "TOPIC": "object_storage_notification",
        "MQTT_BROKER": "broker:1883",
        "MQTT_USER": "user",
        "MQTT_PASSWORD": "pw",
        "MQTT_CLIENT_ID": "cid",
        "MQTT_QOS": "1",
        "MQTT_CLEAN_SESSION": "true",
        "MINIO_URL": "minio:9000",
        "MINIO_ACCESS_KEY": "key",
        "MINIO_SECURE_KEY": "secret",
        "MINIO_SECURE": "false",
        "TOPIC_DATA_PARSED": "data_parsed",
        "DSMDB_DSN": "dsn",
        "DB_API_BASE_URL": "http://fake-db",
        "DB_API_AUTH_TOKEN": "token",
    }.items():
        monkeypatch.setenv(k, v)


@patch("run_file_ingest.DBapi")
@patch("run_file_ingest.Thing")
def test_upload_to_bucket_of_deleted_thing_does_not_exit(
    mock_Thing, mock_DBapi, file_ingest_env
):
    """A thing deleted in the DSM keeps its bucket; uploads must not crash."""
    mock_Thing.from_s3_bucket_name.side_effect = ObjectNotFound(
        "No Thing found for bucket_name='deleted-bucket'"
    )
    handler = ParserJobHandler()
    handler.mqtt_client = MagicMock()
    msg = MQTTMessage(topic=b"object_storage_notification")
    msg.payload = json.dumps(
        {"EventName": "s3:ObjectCreated:Put", "Key": "deleted-bucket/data.csv"}
    ).encode()

    handler.on_message(None, None, msg)  # raised SystemExit before

    mock_Thing.from_s3_bucket_name.assert_called_once()
    handler.mqtt_client.publish.assert_not_called()
