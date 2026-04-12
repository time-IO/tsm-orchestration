#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
from datetime import datetime

import pandas as pd
from paho.mqtt.client import MQTTMessage

from timeio import feta
from timeio.common import get_envvar, setup_logging
from timeio.databases import Database, DBapi
from timeio.errors import (
    DataNotFoundError,
    ParsingError,
    ProcessingError,
)
from timeio.journaling import Journal
from timeio.mqtt import AbstractHandler

from timeio.qc.io import read_stream_data, write_qc_data
from timeio.qc.saqc import SaQCWrapper
from timeio.qc.qcfunction import get_functions, filter_functions
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
        self.dbapi = DBapi(
            get_envvar("DB_API_BASE_URL"),
            get_envvar("DB_API_AUTH_TOKEN"),
        )

    @staticmethod
    def _parse_message_v1(
        conn, content: dict
    ) -> tuple[feta.Project, feta.QAQC | None, feta.Thing]:
        try:
            content = _chkmsg(content, MqttPayload.DataParsedV1, "v1 message")
        except KeyError as e:
            raise ParsingError("Message not in version 1 specs") from e

        thing_uuid = content["thing_uuid"]
        thing = feta.Thing.from_uuid(thing_uuid, dsn=conn)
        project = thing.project
        config = project.get_default_qaqc()
        if config is None:
            logger.info(f"No active QC-Settings found for {project}")
        return project, config, thing

    @staticmethod
    def _parse_message_v2(
        conn, content: dict
    ) -> tuple[feta.Project, feta.QAQC | None, None]:
        try:
            content = _chkmsg(content, MqttPayload.DataParsedV2, "v2 message")
        except KeyError as e:
            raise ParsingError("Message not in version 2 specs") from e

        proj_uuid = content["project_uuid"]
        config_name = content["qc_settings_name"]
        project = feta.Project.from_uuid(proj_uuid, dsn=conn)
        config = (project.get_qaqcs(name=config_name) or [None])[0]
        if config is None:
            logger.info(f"No QC-Settings with name {config_name} found in {project}")
        return project, config, None

    def _parse_message(self, conn, content):
        if (version := content.setdefault("version", 1)) not in {1, 2}:
            raise NotImplementedError(
                f"data_parsed payload version {version} is not supported yet."
            )
        if version == 1:
            logger.info(f"QC was triggered by data upload to thing. {content=}")
            project, config, thing = self._parse_message_v1(conn, content)

        else:
            logger.info(f"QC was triggered by user (or scheduled). {content=}")
            project, config, thing = self._parse_message_v2(conn, content)

        return project, config, thing

    def act(self, content: dict, message: MQTTMessage):

        t0 = datetime.now()

        self.dbapi.ping_dbapi()
        with self.db.connection() as conn:
            logger.debug("successfully connected to configdb")
            project, config, thing = self._parse_message(conn, content)
            if config is None:
                return

            logger.info("Got config {config}")
            try:
                qc_funcs = get_functions(config)
                if thing is not None:
                    qc_funcs = filter_functions(qc_funcs, thing.id)
                logger.info(f"COLLECTED TESTS: {qc_funcs}")
                start_date = pd.Timestamp(content["start_date"])
                end_date = pd.Timestamp(content["end_date"])
            except (NotImplementedError, ValueError, TypeError, ParsingError) as e:
                msg = "Reading QC tests failed"
                if thing:
                    journal.error(f"{msg}, because of {e}", thing.uuid)
                raise ParsingError(msg) from e

            N = len(qc_funcs)
            streams = set(sum([f.streams for f in qc_funcs], []))
            data = read_stream_data(self.dbapi, streams, start_date, end_date)
            for k, v in data.items():
                if v.empty:
                    logger.warning(f"no data found for stream: {k}")
            qc = SaQCWrapper(data)
            for i, func in enumerate(qc_funcs, start=1):
                logger.info("Test %s of %s: %s", i, N, func)
                try:
                    qc.execute(func)
                except Exception as e:
                    msg = f"Executing SaQC function '{func}' failed"
                    if thing:
                        journal.error(f"{msg}, because of {e}", thing.uuid)
                    raise ProcessingError(msg) from e

            write_qc_data(self.dbapi, qc)

        if thing:
            journal.info(
                f"Successfully executed QC Setup {config.name}, which was "
                f"triggered by new data for thing {thing.name} ({thing.uuid})"
                f"in {round((datetime.now() - t0).total_seconds(), 2)} seconds",
                thing.uuid,
            )

        logger.debug("inform downstream services about success of qc.")
        payload = json.dumps(
            {
                "version": 1,
                "project_uuid": project.uuid,
                "thing_uuid": thing and thing.uuid,  # uuid if thing is not None
                "config": config.name,
            }
        )
        self.mqtt_client.publish(
            topic=self.publish_topic, payload=payload, qos=self.publish_qos
        )


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    QcHandler().run_loop()
