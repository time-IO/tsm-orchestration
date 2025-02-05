#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import typing

from paho.mqtt.client import MQTTMessage

from timeio.mqtt import AbstractHandler
from timeio.common import get_envvar, setup_logging
from timeio.errors import UserInputError
from timeio.journaling import Journal
from timeio.databases import ConfigDB, DBapi

logger = logging.getLogger("mqtt-ingest")
journal = Journal("Parser")


class ParseMqttDataHandler(AbstractHandler):
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

        self.confdb = ConfigDB(get_envvar("CONFIGDB_DSN"))
        self.dbapi = DBapi(get_envvar("DB_API_BASE_URL"))

    def act(self, content: typing.Any, message: MQTTMessage):
        topic = message.topic
        origin = f"{self.mqtt_broker}/{topic}"
        logger.info(f"get thing")
        mqtt_user = topic.split("/")[1]
        thing_uuid = self.confdb.get_thing_uuid("mqtt_user", mqtt_user)
        logger.info(f"get parser")
        parser = self.confdb.get_mqtt_parser(thing_uuid)
        logger.info(f"parsing rawdata")
        try:
            data = parser.do_parse(content, origin)
            observations = parser.to_observations(data, thing_uuid)
        except Exception as e:
            raise UserInputError("Parsing data failed") from e
        logger.info(f"store observations")
        self.dbapi.upsert_observations(thing_uuid, observations)
        journal.info(f"parsed mqtt data from {origin}", thing_uuid)


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    ParseMqttDataHandler().run_loop()
