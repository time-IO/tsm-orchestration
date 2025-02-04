#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging

from paho.mqtt.client import MQTTMessage

import databases
from base_handler import AbstractHandler
from qualcontrol import QualityControl
from utils import get_envvar, setup_logging
from utils.errors import DataNotFoundError, UserInputError, NoDataWarning
from utils.journaling import Journal

logger = logging.getLogger("run-quality-control")
journal = Journal("QualityControl")


class QcHandler(AbstractHandler):
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
        self.publish_topic = get_envvar("TOPIC_QC_DONE")
        self.publish_qos = get_envvar("TOPIC_QC_DONE_QOS", cast_to=int)
        self.db = databases.Database(get_envvar("DATABASE_DSN"))
        self.dbapi = databases.DBapi(get_envvar("DB_API_BASE_URL"))

    def act(self, content: dict, message: MQTTMessage):
        if (thing_uuid := content.get("thing_uuid")) is None:
            raise DataNotFoundError(
                "mandatory field 'thing_uuid' is not present in data"
            )
        logger.info(f"Thing {thing_uuid} triggered QAQC service")

        self.dbapi.ping_dbapi()
        with self.db.connection() as conn:
            logger.info("successfully connected to configdb")
            try:
                qaqc = QualityControl(conn, self.dbapi.base_url, thing_uuid)
            except NoDataWarning as w:
                # TODO: uncomment if QC is production-ready
                # journal.warning(str(w), thing_uuid)
                raise w
            try:
                some = qaqc.qacq_for_thing()
            except UserInputError as e:
                journal.error(str(e), thing_uuid)
                raise e
            except NoDataWarning as w:
                journal.warning(str(w), thing_uuid)
                raise w

        if some:
            journal.info(f"QC done. Config: {qaqc.conf['name']}", thing_uuid)
        else:
            journal.warning(
                f"QC done, but no quality labels were generated. "
                f"Config: {qaqc.conf['name']}",
                thing_uuid,
            )
            return

        logger.debug(f"inform downstream services about success of qc.")
        payload = json.dumps({"thing": thing_uuid})
        self.mqtt_client.publish(
            topic=self.publish_topic, payload=payload, qos=self.publish_qos
        )


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    QcHandler().run_loop()
