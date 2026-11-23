#!/usr/bin/env python3

import pytest
from paho.mqtt.client import MQTTMessage
from unittest.mock import MagicMock

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


def make_handler(topic):
    class H(RecordingHandler):
        def __init__(self):
            AbstractHandler.__init__(
                self,
                topic=topic,
                mqtt_broker="broker:1883",
                mqtt_user="user",
                mqtt_password="pw",
                mqtt_client_id="cid",
                mqtt_qos=1,
                mqtt_clean_session=True,
            )
            self.received = []

    handler = H()
    handler.mqtt_client = MagicMock()
    handler.mqtt_client.subscribe.side_effect = [
        (0, i) for i in range(1, 10)
    ]  # (result, mid), one per call
    return handler


def test_single_topic_as_text_is_subscribed_as_before():
    handler = make_handler("a/b")

    handler.on_connect(handler.mqtt_client, None, None, 0)

    calls = [c.args for c in handler.mqtt_client.subscribe.call_args_list]
    assert calls[0] == ("a/b", 1)


def test_all_topics_of_a_list_are_subscribed_with_the_handler_qos():
    handler = make_handler(["a/b", "c/d"])

    handler.on_connect(handler.mqtt_client, None, None, 0)

    calls = [c.args for c in handler.mqtt_client.subscribe.call_args_list]
    assert ("a/b", 1) in calls
    assert ("c/d", 1) in calls


def test_each_subscription_is_registered_for_logging():
    handler = make_handler(["a/b", "c/d"])

    handler.on_connect(handler.mqtt_client, None, None, 0)

    assert set(handler._mid_to_topic.values()) >= {"a/b", "c/d"}


def test_healthcheck_topic_is_still_subscribed():
    handler = make_handler(["a/b", "c/d"])

    handler.on_connect(handler.mqtt_client, None, None, 0)

    calls = [c.args for c in handler.mqtt_client.subscribe.call_args_list]
    assert (handler._healthcheck_topic, 0) in calls
