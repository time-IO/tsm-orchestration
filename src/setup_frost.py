import logging

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.typehints import MqttPayload
from timeio import frost

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
        self.dsmdb_dsn = get_envvar("DSMDB_DSN")
        self.api_url = get_envvar("FROST_CONTEXT_API_URL")
        self.internal_api_url = get_envvar("FROST_INTERNAL_CONTEXT_API_URL")
        self.api_token = get_envvar("FROST_CONTEXT_API_TOKEN")

    def act(self, content: MqttPayload.UpdateThing, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.dsmdb_dsn)
        db = thing.database
        # sti_ user's search_path points at the internal schema (setup_user_database.py)
        targets = [
            ("public", self.api_url, "sta_"),
            ("internal", self.internal_api_url, "sti_"),
        ]
        failed = []
        for name, api_url, prefix in targets:
            try:
                xml = frost.render_context(
                    schema=db.schema,
                    user=f"{prefix}{db.ro_username.lower()}",
                    password=db.ro_password,
                    db_url=db.ro_url,
                    tomcat_proxy_url=self.tomcat_proxy_url,
                )
                frost.push_context(api_url, self.api_token, db.schema, xml)
            except Exception as e:
                failed.append(f"{name}: {e}")
        if failed:
            raise RuntimeError(f"FROST context push failed for {'; '.join(failed)}")


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateFrostInstanceHandler().run_loop()
