import logging

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.thing import Thing
from timeio.common import get_envvar, setup_logging

logger = logging.getLogger("frost-setup")


class CreateFrostInstanceHandler(AbstractHandler):

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
        self.tomcat_proxy_url = get_envvar("TOMCAT_PROXY_URL")

    def act(self, content: dict, message: MQTTMessage):
        thing = Thing.get_instance(content)
        thing.setup_frost(self.tomcat_proxy_url)


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateFrostInstanceHandler().run_loop()
