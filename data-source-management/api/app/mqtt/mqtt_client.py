from __future__ import annotations

import logging
import json
import socket
import time
from threading import get_native_id

import paho.mqtt.client as mqtt

from config import settings
from .generate_mqtt_messages import (
    create_sync_ext_api_msg,
    create_sync_ext_sftp_msg,
    create_sync_quality_control,
    create_frontend_thing_update,
    create_qc_settings_msg,
)

logger = logging.getLogger("app.mqtt")

client: mqtt.Client | None = None


def on_connect(client, userdata, flags, reason_code, properties=None):
    logger.info(f"Connected to MQTT broker: {client.host} | port: {client.port}")


def on_publish(client, userdata, mid, reason_code=None, properties=None):
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
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        protocol=mqtt.MQTTv5,
        client_id=f"{mqtt_config['client_id']}-{postfix}",
    )
    client.username_pw_set(mqtt_config["user"], mqtt_config["password"])
    client.on_connect = on_connect
    client.on_publish = on_publish

    try:
        logger.debug(
            "Connecting MQTT client id=%s host=%s port=%s",
            client._client_id.decode(),
            mqtt_config["broker_host"],
            mqtt_config["broker_port"],
        )
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
    logger.debug(
        "Publishing MQTT message to topic='%s' qos=%s payload_keys=%s",
        topic,
        qos,
        sorted(msg.keys()),
    )
    result = client.publish(topic, json.dumps(msg), qos=qos)
    result.wait_for_publish(5)
    logger.info(success_log)


def publish_trigger_quality_control(
    permission_group_uuid,
    qc_settings_name,
    start_date,
    end_date,
    topic="run_qc_triggered",
):
    msg = create_sync_quality_control(
        permission_group_uuid, qc_settings_name, start_date, end_date
    )
    publish_message(
        msg,
        topic,
        f"Quality control triggered for ingest '{permission_group_uuid}' with QC settings '{qc_settings_name}' published on '{topic}'",
    )


def publish_trigger_ext_api(
    ingest_uuid, date_from, date_to, topic="sync_ext_apis_triggered"
):
    msg = create_sync_ext_api_msg(ingest_uuid, date_from, date_to)
    publish_message(
        msg,
        topic,
        f"External API sync for ingest '{ingest_uuid}' published on '{topic}'",
    )


def publish_trigger_ext_sftp(
    ingest_uuid, datetime_from, datetime_to, topic="sync_ext_sftp"
):
    msg = create_sync_ext_sftp_msg(ingest_uuid, datetime_from, datetime_to)
    publish_message(
        msg,
        topic,
        f"External SFTP sync for ingest '{ingest_uuid}' published on '{topic}'",
    )


def publish_frontend_thing_update(ingest, topic="frontend_thing_update"):
    msg = create_frontend_thing_update(ingest)
    publish_message(
        msg, topic, f"Ingest with UUID '{ingest.uuid}' published on '{topic}'"
    )


def publish_qaqc_settings_update(qc_settings, topic="qaqc_settings_update"):
    msg = create_qc_settings_msg(qc_settings)
    publish_message(
        msg, topic, f"QC Settings '{qc_settings.name}' published on '{topic}'"
    )
