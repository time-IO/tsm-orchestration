#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging

from paho.mqtt.client import MQTTMessage

from timeio.mqtt import AbstractHandler
from timeio.qualcontrol import QualityControl
from timeio.common import get_envvar, setup_logging
from timeio.errors import DataNotFoundError, UserInputError, NoDataWarning
from timeio.journaling import Journal
from timeio.databases import Database, DBapi
from timeio.typehints import MqttPayload, check_dict_by_TypedDict as _chkmsg

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
        self.db = Database(get_envvar("DATABASE_DSN"))
        self.dbapi = DBapi(get_envvar("DB_API_BASE_URL"))

    def _check_data(self, content, keys: list[str]):
        for key in keys:
            if key not in content:
                raise DataNotFoundError(
                    "mandatory field '{key}' is not present in data"
                )

    def act(self, content: dict, message: MQTTMessage):
        thing_uuid = None
        version = content.setdefault("version", 1)
        if version == 1:
            _chkmsg(content, MqttPayload.DataParsedV1, "data-parsed message v1")
            thing_uuid = content["thing_uuid"]
            logger.info(f"QC was triggered by data upload to thing. {content=}")
        elif version == 2:
            _chkmsg(content, MqttPayload.DataParsedV2, "data-parsed message v2")
            logger.info(f"QC was triggered by user (in frontend). {content=}")
        else:
            raise NotImplementedError(
                f"data_parsed payload version {version} is not supported yet."
            )

        self.dbapi.ping_dbapi()
        with self.db.connection() as conn:
            logger.info("successfully connected to configdb")
            if version == 1:
                content: MqttPayload.DataParsedV1
                qc = QualityControl.from_thing(
                    conn,
                    self.dbapi.base_url,
                    uuid=thing_uuid,
                )
            else:
                content: MqttPayload.DataParsedV2
                qc = QualityControl.from_project(
                    conn,
                    self.dbapi.base_url,
                    uuid=content["project_uuid"],
                    config_name=content["qc_settings_name"],
                )
            try:
                if qc.legacy:
                    # A legacy workflow should only be possible with v1
                    # and must deliver a thing_uuid (because it works on
                    # a single thing).
                    assert version == 1 and thing_uuid is not None
                    some = qc.run_legacy(thing_uuid)
                else:
                    some = qc.run(content.get("start_date"), content.get("end_date"))
            except UserInputError as e:
                if thing_uuid is not None:
                    journal.error(str(e), thing_uuid)
                raise e
            except NoDataWarning as w:
                if thing_uuid is not None:
                    journal.warning(str(w), thing_uuid)
                raise w

        if thing_uuid is not None:
            if some:
                journal.info(f"QC done. Config: {qc.conf.name}", thing_uuid)
            else:
                journal.warning(
                    f"QC done, but no quality labels were generated. "
                    f"Config: {qc.conf.name}",
                    thing_uuid,
                )
                return

        logger.debug(f"inform downstream services about success of qc.")
        payload = json.dumps(
            {
                "version": 1,
                "project_uuid": qc.proj.uuid,
                "thing_uuid": thing_uuid,  # None allowed
            }
        )
        self.mqtt_client.publish(
            topic=self.publish_topic, payload=payload, qos=self.publish_qos
        )


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    QcHandler().run_loop()
