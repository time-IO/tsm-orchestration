import logging
from urllib.parse import urlparse, urlunparse

import requests

from timeio.crypto import decrypt, get_crypt_key
from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.typehints import MqttPayload

logger = logging.getLogger("frost-setup")


def push_context(
    api_url: str, token: str, schema: str, user: str, password: str, db_url: str
) -> None:
    """PUT a context's DB connection to a FROST context API; `password` is encrypted."""
    parts = urlparse(db_url)
    hostname = parts.hostname
    if parts.port:
        hostname += f":{parts.port}"
    url = f"{api_url.rstrip('/')}/contexts/{schema}"
    logger.debug(f"push tomcat context {schema!r} to {url!r}")
    resp = requests.put(
        url,
        data={
            "user": user,
            "password": decrypt(password, get_crypt_key()),
            "url": urlunparse((parts.scheme, hostname, parts.path, "", "", "")),
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if not resp.ok:
        # the API's error body names the rejected field
        raise requests.HTTPError(
            f"{resp.status_code} {resp.reason} for {url}: {resp.text[:200]}",
            response=resp,
        )


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
                push_context(
                    api_url,
                    self.api_token,
                    schema=db.schema,
                    user=f"{prefix}{db.ro_username.lower()}",
                    password=db.ro_password,
                    db_url=db.ro_url,
                )
            except Exception as e:
                logger.exception(f"FROST context push failed for {name}")
                failed.append(f"{name}: {e}")
        if failed:
            raise RuntimeError(f"FROST context push failed for {'; '.join(failed)}")


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateFrostInstanceHandler().run_loop()
