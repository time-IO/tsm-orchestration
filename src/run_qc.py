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
    ) -> tuple[feta.Project, list[feta.QAQC] | None, feta.Thing]:
        try:
            content = _chkmsg(content, MqttPayload.DataParsedV1, "v1 message")
        except KeyError as e:
            raise ParsingError("Message not in version 1 specs") from e

        thing_uuid = content["thing_uuid"]
        thing = feta.Thing.from_uuid(thing_uuid, dsn=conn)
        project = thing.project
        configs = project.get_default_qaqcs()
        if configs is None:
            logger.info(f"No active QC-Settings found for {project}")
        return project, configs, thing

    @staticmethod
    def _parse_message_v2(
        conn, content: dict
    ) -> tuple[feta.Project, list[feta.QAQC] | None, None]:
        try:
            content = _chkmsg(content, MqttPayload.DataParsedV2, "v2 message")
        except KeyError as e:
            raise ParsingError("Message not in version 2 specs") from e

        proj_uuid = content["project_uuid"]
        config_name = content["qc_settings_name"]
        project = feta.Project.from_uuid(proj_uuid, dsn=conn)
        configs = project.get_qaqcs(name=config_name)
        if configs is None:
            logger.info(f"No QC-Settings with name {config_name} found in {project}")
        return project, configs, None

    def _parse_message(
        self, conn, content
    ) -> tuple[feta.Project, list[feta.QAQC] | None, feta.Thing | None]:
        version = content.setdefault("version", 1)
        if version == 1:
            logger.info(f"QC was triggered by data upload to thing. {content=}")
            project, config, thing = self._parse_message_v1(conn, content)

        elif version == 2:
            logger.info(f"QC was triggered by user (or scheduled). {content=}")
            project, config, thing = self._parse_message_v2(conn, content)
        else:
            raise NotImplementedError(
                f"data_parsed payload version {version} is not supported yet."
            )
        return project, config, thing

    def act(self, content: dict, message: MQTTMessage):

        t0 = datetime.now()

        self.dbapi.ping_dbapi()
        with self.db.connection() as conn:
            logger.debug("successfully connected to configdb")
            project, configs, thing = self._parse_message(conn, content)
            if configs is None:
                return

            logger.info(f"Got the following configurations {configs}")
            qc_funcs = get_functions(configs)
            if not qc_funcs:
                return
            if thing is not None:
                qc_funcs = filter_functions(qc_funcs, thing.id)
            else:
                # NOTE:
                # We don't have a thing, if the qc run was manually triggered.
                # As we need a thing to write information to the journal, we
                # just select the first thing used in the setting
                # TODO:
                # Remove if we have a project wide journal endpoint
                thing = feta.Thing.from_uuid(
                    qc_funcs[0].streams[0].thing_uuid, dsn=conn
                )
            logger.info(f"COLLECTED TESTS: {qc_funcs}")
            start_date = pd.Timestamp(content["start_date"])
            end_date = pd.Timestamp(content["end_date"])

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
                    journal.error(f"{msg}, because of {e}", thing.uuid)
                    raise ProcessingError(msg) from e

            write_qc_data(self.dbapi, qc)

        config_names = [c.name for c in configs]
        journal.info(
            f"Successfully executed the following QC Setups: {config_names} "
            f"in {round((datetime.now() - t0).total_seconds(), 2)} seconds",
            thing.uuid,
        )

        logger.debug("inform downstream services about success of qc.")
        payload = json.dumps(
            {
                "version": 1,
                "project_uuid": project.uuid,
                "config": config_names,
            }
        )
        self.mqtt_client.publish(
            topic=self.publish_topic, payload=payload, qos=self.publish_qos
        )


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    QcHandler().run_loop()
