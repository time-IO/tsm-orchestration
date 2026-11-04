from __future__ import annotations

import logging

from minio import Minio

from timeio.common import get_envvar, setup_logging
from timeio.feta import Thing
from timeio.journaling import Journal
from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.reparse import make_publisher, parser_exists, reparse_files
from timeio.typehints import MqttPayload

logger = logging.getLogger("reparse-files")
journal = Journal("Reparse", errors="warn")


class ReparseFilesManager(AbstractHandler):

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
        minio_secure = get_envvar("MINIO_SECURE").lower() not in ["false", "0"]
        self.minio = Minio(
            endpoint=get_envvar("MINIO_URL"),
            access_key=get_envvar("MINIO_USER"),
            secret_key=get_envvar("MINIO_PASSWORD"),
            secure=minio_secure,
        )

    def act(self, content: MqttPayload.ReparsesFiles, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.dsmdb_dsn)

        parser_uuid = content.get("parser_uuid")
        if parser_uuid and not parser_exists(parser_uuid, self.dsmdb_dsn):
            msg = f"Reparsing not started: parser {parser_uuid} does not exist."
            logger.error(msg)
            journal.error(msg, thing.uuid)
            return

        # A second client with its own network thread sends the messages, so that
        # waiting for acknowledgements cannot block this handler's client.
        publisher = make_publisher(
            self.mqtt_broker,
            self.mqtt_user,
            self.mqtt_password,
            f"{self.mqtt_client_id}-publisher",
        )
        try:
            reparse_files(
                thing,
                self.minio,
                publisher,
                journal,
                self.dsmdb_dsn,
                start_date=content.get("start_date"),
                end_date=content.get("end_date"),
                filename_pattern=content.get("filename_pattern"),
                parser_uuid=parser_uuid,
                include_parsed=content.get("include_parsed", False),
                parsed_files_parser=content.get("parsed_files_parser", "current"),
            )
        except Exception as e:
            journal.error(f"Reparsing aborted: {e}", thing.uuid)
            raise
        finally:
            publisher.loop_stop()
            publisher.disconnect()


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    ReparseFilesManager().run_loop()
