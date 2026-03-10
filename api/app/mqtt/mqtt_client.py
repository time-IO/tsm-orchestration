from __future__ import annotations

import logging
import json
import socket
import time
from threading import get_native_id

import paho.mqtt.client as mqtt

from config import settings

logger = logging.getLogger("app.mqtt")

client: mqtt.Client | None = None


def on_connect(client, userdata, flags, reason_code, properties=None):
    logger.info(f"Connected to MQTT broker: {client.host} | port: {client.port}")


def on_publish(client, userdata, mid, result=None, properties=None):
    logger.info("Message with id: {} published.".format(mid))


mqtt_config = {
    "broker_host": settings.MQTT_BROKER_HOST,
    "broker_port": settings.MQTT_PORT,
    "client_id": settings.MQTT_CLIENT_ID,
    "user": settings.MQTT_USER,
    "password": settings.MQTT_PASSWORD,
    "qos": settings.MQTT_QOS,
}


def mk_client():
    global client
    # We need a unique client id for each frontend thread/process.
    # Otherwise, we get a race-condition and each new client dis-
    # connects its predecessor.
    postfix = get_native_id()
    client = mqtt.Client(
        protocol=mqtt.MQTTv5,
        client_id=f"{mqtt_config['client_id']}-{postfix}",
    )
    client.username_pw_set(mqtt_config["user"], mqtt_config["password"])
    client.on_connect = on_connect
    client.on_publish = on_publish

    try:
        client.connect(host=mqtt_config["broker_host"], port=mqtt_config["broker_port"])
    except (socket.gaierror, ConnectionRefusedError) as e:
        raise ConnectionError(
            f"Unable to connect to mqtt broker {mqtt_config['broker_host']} "
            f"on port {mqtt_config['broker_port']}"
        ) from e

    # Spawn an own client thread, which handle
    # ACKs from broker when using QOS>0.
    client.loop_start()


def publish_message(msg: dict, topic: str, success_log: str):
    if client is None:
        mk_client()
        time.sleep(1)
    if not client.is_connected():
        raise ConnectionError(
            f"Unable to publish MQTT message to broker at {mqtt_config['broker_host']}. "
            "Client not connected."
        )
    qos = mqtt_config.get("qos")
    result = client.publish(topic, json.dumps(msg), qos=qos)
    result.wait_for_publish(5)
    logger.info(success_log)
