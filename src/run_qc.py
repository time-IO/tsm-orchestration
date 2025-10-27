#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging

import pandas as pd
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

    @staticmethod
    def get_config_from_project(
        project: feta.Project, config_name: str | None = None
    ) -> feta.QAQC | None:
        pass

    @staticmethod
    def parse_version1(
        conn, content: MqttPayload.DataParsedV1
    ) -> tuple[feta.Project, feta.QAQC | None, str]:
        thing_uuid = content["thing_uuid"]
        thing = feta.Thing.from_uuid(thing_uuid, dsn=conn)
        project = thing.project
        config = project.get_default_qaqc()
        if config is None:
            logger.info(f"No active QC-Settings found for {project}")
        return project, config, thing_uuid

    @staticmethod
    def parse_version2(
        conn, content: MqttPayload.DataParsedV2
    ) -> tuple[feta.Project, feta.QAQC | None, None]:
        proj_uuid = content["project_uuid"]
        config_name = content["qc_settings_name"]
        project = feta.Project.from_uuid(proj_uuid, dsn=conn)
        config = (project.get_qaqcs(name=config_name) or [None])[0]
        if config is None:
            logger.info(f"No QC-Settings with name {config_name} found in {project}")
        return project, config, None

    def act(self, content: dict, message: MQTTMessage):

        if (version := content.setdefault("version", 1)) not in [1,2]:
            raise NotImplementedError(
                f"data_parsed payload version {version} is not supported yet."
            )

        self.dbapi.ping_dbapi()
        with self.db.connection() as conn:
            logger.debug("successfully connected to configdb")

            if version == 1:
                content = _chkmsg(content, MqttPayload.DataParsedV1, "data-parsed message v1")
                logger.info(f"QC was triggered by data upload to thing. {content=}")
                project, config, thing_uuid = self.parse_version1(conn, content)

            else:
                content =_chkmsg(content, MqttPayload.DataParsedV2, "data-parsed message v2")
                logger.info(f"QC was triggered by user (in frontend). {content=}")
                project, config, thing_uuid = self.parse_version2(conn, content)

            if config is None:
                return

            logger.info(f"Got config %s", config)
            sm = StreamManager(conn)
            tests = collect_tests(config)

            if start_date := content.get("start_date", None):
                start_date = pd.Timestamp(start_date)
            if end_date := content.get("end_date", None):
                end_date = pd.Timestamp(end_date)

            N = len(tests)
            for i, test in enumerate(tests, start=1):  # type: QcTest
                logger.info("Test %s of %s: %s", i, N, test)
                test.parse()
                test.load_data(sm, start_date, end_date)
                test.run()
                sm.update(test.result)

            sm.upload(self.dbapi.base_url)

        logger.debug(f"inform downstream services about success of qc.")
        payload = json.dumps(
            {
                "version": 1,
                "project_uuid": project.uuid,
                "thing_uuid": thing_uuid,  # None allowed
                "config": config.name,
            }
        )
        self.mqtt_client.publish(
            topic=self.publish_topic, payload=payload, qos=self.publish_qos
        )


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    QcHandler().run_loop()
