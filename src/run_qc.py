#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging

from paho.mqtt.client import MQTTMessage
from psycopg import Connection

from timeio import feta
from timeio.common import get_envvar, setup_logging
from timeio.databases import Database, DBapi
from timeio.errors import DataNotFoundError, NoDataWarning
from timeio.journaling import Journal
from timeio.mqtt import AbstractHandler
from timeio.qc import QcTest, StreamManager, collect_tests
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

    @classmethod
    def get_config_from_thing(cls, conn: Connection, thing_uuid: str):
        thing = feta.Thing.from_uuid(thing_uuid, dsn=conn)
        proj = thing.project
        qc = proj.get_default_qaqc() or thing.get_legacy_qaqc()
        if qc is None:
            raise NoDataWarning(
                f"Neither found active QC-Settings for project {proj.name}, "
                f"nor legacy QC-Settings for thing {thing.name}."
            )
        return qc

    def get_config_from_project(
        self, conn: Connection, proj_uuid: str, config_name: str | None = None
    ):
        proj = feta.Project.from_uuid(proj_uuid, dsn=conn)
        if config_name is None:
            if (qc := proj.get_default_qaqc()) is None:
                raise NoDataWarning(
                    f"No active QC-Settings found in project {proj.name}"
                )
        else:
            if not (qcs := proj.get_qaqcs(name=config_name)):
                raise DataNotFoundError(
                    f"No QC-Settings with name {config_name} "
                    f"found in project {proj.name}"
                )
            qc = qcs[0]
        return qc

    def act(self, content: dict, message: MQTTMessage):
        version = content.setdefault("version", 1)
        if version == 1:  # data was parsed
            _chkmsg(content, MqttPayload.DataParsedV1, "data-parsed message v1")
            logger.info(f"QC was triggered by data upload to thing. {content=}")
        elif version == 2:  # triggered by frontend
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
                thing_uuid = content["thing_uuid"]
                config = self.get_config_from_thing(conn, thing_uuid)
                proj_uuid = config.project.uuid
            else:
                content: MqttPayload.DataParsedV2
                thing_uuid = None
                proj_uuid = content["project_uuid"]
                config_name = content["qc_settings_name"]
                config = self.get_config_from_project(conn, proj_uuid, config_name)

            sm = StreamManager(conn)
            tests = collect_tests(config)
            start_date = content.get("start_date", None)
            end_date = content.get("end_date", None)

            for test in tests:  # type: QcTest
                test.parse()
                test.load_data(sm, start_date, end_date)
                test.run()
                sm.update(test.result)

            sm.upload()

        logger.debug(f"inform downstream services about success of qc.")
        payload = json.dumps(
            {
                "version": 1,
                "project_uuid": proj_uuid,
                "thing_uuid": thing_uuid,  # None allowed
            }
        )
        self.mqtt_client.publish(
            topic=self.publish_topic, payload=payload, qos=self.publish_qos
        )


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    QcHandler().run_loop()
