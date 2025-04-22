from __future__ import annotations

import logging


from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.common import get_envvar, setup_logging
from timeio.typehints import MqttPayload
from timeio.sms import SmsMaterializedViewsSyncer, SmsCVSyncer

logger = logging.getLogger("sync-sms-manager")


class SyncSmsManager(AbstractHandler):

    def __init__(self):
        super().__init__(
            topic=get_envvar("TOPIC"),
            mqtt_broker=get_envvar("MQTT_BROKER"),
            mqtt_user=get_envvar("MQTT_USER"),
            mqtt_password=get_envvar("MQTT_PASSWORD"),
            mqtt_client_id=get_envvar("MQTT_CLIENT_ID"),
            mqtt_qos=get_envvar("MQTT_QOS", cast_to=int),
            mqtt_clean_session=get_envvar("MQTT_CLEAN_SESSION", cast_to=bool),
        )

    def act(self, content: MqttPayload.SyncSmsT, message: MQTTMessage):
        origin = content["origin"]
        if origin == "sms_backend":
            SmsMaterializedViewsSyncer().collect_materialized_views().update_materialized_views()
        elif origin == "sms_cv":
            SmsCVSyncer().sync()


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    SyncSmsManager().run_loop()
