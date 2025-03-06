from __future__ import annotations

import logging

from sync_tsystems_api import SyncTsystemsApi
from sync_bosch_api import SyncBoschApi

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.common import get_envvar, setup_logging
from timeio.feta import Thing
from timeio.typehints import MqttPayload

logger = logging.getLogger("sync-extapi-manager")


class SyncExtApiManager(AbstractHandler):

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
        self.configdb_dsn = get_envvar("CONFIGDB_DSN")
        self.sync_handlers = {"tsystems": SyncTsystemsApi(), "bosch": SyncBoschApi()}

    def act(self, content: MqttPayload.SyncExtApi, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.configdb_dsn)
        ext_api_name = thing.ext_api.api_type_name

        if ext_api_name in self.sync_handlers:
            logger.info(f"Start ext_api sync for API '{ext_api_name}'")
            self.sync_handlers[ext_api_name].sync(thing, content)
        else:
            logger.warning(f"No handler found for ext_api_type '{ext_api_name}'")


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    SyncExtApiManager().run_loop()
