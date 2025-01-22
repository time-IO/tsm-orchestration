#!/usr/bin/env python3

import os
import paho.mqtt.publish

try:
    _broker = os.environ["MQTT_BROKER"]
    mqtt_setting = {
        "qos": int(os.environ["MQTT_QOS"]),
        "hostname": _broker.split(":")[0],
        "port": int(_broker.split(":")[1]),
        "client_id": os.environ["MQTT_QOS"],
        "auth": {
            "username": os.environ["MQTT_USER"],
            "password": os.environ["MQTT_PASSWORD"],
        },
    }
except KeyError as e:
    raise EnvironmentError(f"Missing environment variable {e}")


def send_mqtt_info(topic, payload: str):
    """
    Publish a single mqtt message to a broker, then disconnect cleanly.
    """
    paho.mqtt.publish.single(**mqtt_setting, topic=topic, payload=payload)
