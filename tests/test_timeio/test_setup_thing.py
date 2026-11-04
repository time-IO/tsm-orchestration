#!/usr/bin/env python3

from unittest.mock import MagicMock, patch

import pytest
from paho.mqtt.client import MQTTMessage

from setup_thing import SetupThingHandler

calls = []


class OkStep:
    def act(self, content, message):
        calls.append("ok")


class FailingStep:
    def act(self, content, message):
        raise RuntimeError("connection to postgresql://admin:secret@db failed")


@pytest.fixture
def handler(monkeypatch):
    for k, v in {
        "TOPIC": "frontend_thing_update",
        "MQTT_BROKER": "broker:1883",
        "MQTT_USER": "user",
        "MQTT_PASSWORD": "pw",
        "MQTT_CLIENT_ID": "cid",
        "MQTT_QOS": "1",
        "MQTT_CLEAN_SESSION": "true",
    }.items():
        monkeypatch.setenv(k, v)
    steps = {"first": OkStep, "broken": FailingStep, "last": OkStep}
    calls.clear()
    with patch.dict(SetupThingHandler.HANDLERS, steps, clear=True):
        yield SetupThingHandler(list(steps))


@patch("setup_thing.journal")
def test_failed_step_is_journaled_and_others_still_run(mock_journal, handler):
    handler.act({"thing": "UUID"}, MQTTMessage(topic=b"frontend_thing_update"))

    assert calls == ["ok", "ok"]
    mock_journal.error.assert_called_once()
    message, thing_uuid = mock_journal.error.call_args.args
    assert thing_uuid == "UUID"
    assert "'broken'" in message and "RuntimeError" in message
    assert "secret" not in message


@patch("setup_thing.journal")
def test_successful_setup_journals_no_error(mock_journal, handler):
    handler.handlers = [(n, h) for n, h in handler.handlers if n != "broken"]
    handler.act({"thing": "UUID"}, MQTTMessage(topic=b"frontend_thing_update"))

    assert calls == ["ok", "ok"]
    mock_journal.error.assert_not_called()
