"""Live MQTT inspection for MQTT ingests.

Each open MQTT-client dialog gets its own :class:`MqttSubscriber` — a dedicated
paho client that connects to the broker as the ingest's own MQTT user, subscribes
(QoS 0) to the ingest's topic tree ``mqtt_ingest/<username>/#`` and hands received
messages to an ``asyncio.Queue`` that the WebSocket handler drains. Because every
session has its own client (with an identifiable, unique client id), any number of
users can watch the same ingest at once; the broker fans messages out to all of
them. Publishing (also QoS 0) reuses the same client.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from config import settings

logger = logging.getLogger("app.services.mqtt_inspect")

# Drop payloads larger than this (protects the browser); a note is appended.
MAX_PAYLOAD_CHARS = 10_000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MqttSubscriber:
    """One paho client bound to a single WebSocket session."""

    def __init__(self, *, username: str, password: str, topic: str, loop, queue):
        self.username = username
        self.password = password
        self.topic = topic  # e.g. "mqtt_ingest/<username>"
        self._loop = loop
        self._queue: asyncio.Queue = queue
        self.dropped = 0
        self._client: mqtt.Client | None = None

    def start(self) -> None:
        # Identifiable per-ingest client id, unique per session so concurrent
        # viewers of the same ingest don't evict each other on the broker.
        client_id = f"dsm-mqtt-inspect-{self.username}-{uuid.uuid4().hex[:8]}"
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            protocol=mqtt.MQTTv5,
            client_id=client_id,
        )
        client.username_pw_set(self.username, self.password)
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_PORT)
        client.loop_start()
        self._client = client
        logger.debug("MQTT inspect subscriber started: client_id=%s", client_id)

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        client.subscribe(f"{self.topic}/#", qos=0)
        logger.debug("Subscribed to %s/# (qos=0)", self.topic)

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace")
        if len(payload) > MAX_PAYLOAD_CHARS:
            payload = payload[:MAX_PAYLOAD_CHARS] + "…(truncated)"
        item = {
            "type": "message",
            "topic": msg.topic,
            "payload": payload,
            "received_at": _now_iso(),
        }
        # on_message runs in paho's network thread; hop to the event loop thread.
        self._loop.call_soon_threadsafe(self._enqueue, item)

    def _enqueue(self, item: dict) -> None:
        try:
            self._queue.put_nowait(item)
        except asyncio.QueueFull:
            # keep the newest: drop the oldest and count it
            try:
                self._queue.get_nowait()
                self.dropped += 1
                self._queue.put_nowait(item)
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass

    def publish(self, topic_suffix: str, payload: str) -> str:
        if self._client is None:
            raise RuntimeError("subscriber not started")
        suffix = (topic_suffix or "").strip().strip("/")
        topic = self.topic if not suffix else f"{self.topic}/{suffix}"
        self._client.publish(topic, payload, qos=0)
        return topic

    def stop(self) -> None:
        if self._client is not None:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:  # pragma: no cover - best-effort teardown
                logger.debug("Error stopping MQTT inspect subscriber", exc_info=True)
            self._client = None
