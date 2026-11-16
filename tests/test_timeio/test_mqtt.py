#!/usr/bin/env python3

import pytest
from paho.mqtt.client import MQTTMessage

from timeio.mqtt import AbstractHandler


class RecordingHandler(AbstractHandler):
    def __init__(self):
        super().__init__(
            topic="test/topic",
            mqtt_broker="broker:1883",
            mqtt_user="user",
            mqtt_password="pw",
            mqtt_client_id="cid",
            mqtt_qos=1,
            mqtt_clean_session=True,
        )
        self.received = []

    def act(self, content, message):
        self.received.append(content)


def make_message(payload: bytes) -> MQTTMessage:
    msg = MQTTMessage(topic=b"test/topic")
    msg.payload = payload
    return msg


def test_on_message_passes_decoded_json_to_act():
    handler = RecordingHandler()
    handler.on_message(None, None, make_message(b'{"thing": "abc"}'))
    assert handler.received == [{"thing": "abc"}]


def test_on_message_drops_non_utf8_payload_without_exiting():
    handler = RecordingHandler()
    handler.on_message(None, None, make_message(b"\xff\xfe\x00binary"))
    assert handler.received == []


def test_on_message_keeps_running_after_non_utf8_payload():
    handler = RecordingHandler()
    handler.on_message(None, None, make_message(b"\xff\xfe"))
    handler.on_message(None, None, make_message(b'"next"'))
    assert handler.received == ["next"]


def test_on_message_exits_on_unhandled_error_in_act():
    class FailingHandler(RecordingHandler):
        def act(self, content, message):
            raise RuntimeError("boom")

    handler = FailingHandler()
    with pytest.raises(SystemExit):
        handler.on_message(None, None, make_message(b"{}"))
