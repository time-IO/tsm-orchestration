from __future__ import annotations

import fnmatch
import json
import logging
from datetime import datetime
import warnings
import requests

from minio import Minio
from minio.commonconfig import Tags

from timeio.common import get_envvar, setup_logging
from timeio.errors import UserInputError, ParsingError, ParsingWarning
from timeio.feta import Thing
from timeio.journaling import Journal
from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.parser import get_parser

_FILE_MAX_SIZE = 256 * 1024 * 1024

logger = logging.getLogger("file-ingest")
journal = Journal("Parser", errors="warn")


class ParserJobHandler(AbstractHandler):

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
        self.minio = Minio(
            endpoint=get_envvar("MINIO_URL"),
            access_key=get_envvar("MINIO_ACCESS_KEY"),
            secret_key=get_envvar("MINIO_SECURE_KEY"),
            secure=get_envvar("MINIO_SECURE", default=True, cast_to=bool),
        )
        self.pub_topic = get_envvar("TOPIC_DATA_PARSED")
        self.api_base_url = get_envvar("DB_API_BASE_URL")
        self.configdb_dsn = get_envvar("CONFIGDB_DSN")

    def act(self, content: dict, message: MQTTMessage):

        if not self.is_valid_event(content):
            logger.debug(f'irrelevant event {content["EventName"]!r}')
            return

        # Directories are part of the filename
        # eg: foo/bar/file.ext -> bucket: foo, file: bar/file.ext
        bucket_name, filename = content["Key"].split("/", maxsplit=1)

        thing = Thing.from_s3_bucket_name(bucket_name, dsn=self.configdb_dsn)
        thing_uuid = thing.uuid
        schema = thing.project.database.schema
        pattern = thing.s3_store.filename_pattern
        tags = self.get_parser_tags(bucket_name, filename)
        if tags is not None:
            parser_id = int(tags["parser_id"])
            logger.info(f"Re-parsing file with parser from file tag {parser_id}")
        else:
            parser_id = thing.s3_store.file_parser_id
            logger.info(f"No parser file tag found, using default parser {parser_id=}")

        if not fnmatch.fnmatch(filename, pattern):
            logger.debug(f"{filename} is excluded by filename_pattern {pattern!r}")
            return
        source_uri = f"{bucket_name}/{filename}"

        logger.debug(f"loading parser for {thing_uuid}")

        pobj = thing.s3_store.file_parser
        parser = get_parser(pobj.file_parser_type.name, pobj.params)

        logger.debug(f"reading raw data file {source_uri}")
        rawdata = self.read_file(bucket_name, filename)

        logger.info("parsing rawdata ... ")
        file = "/".join(source_uri.split("/")[1:])  # remove bucket name from source_uri
        with warnings.catch_warnings(record=True) as recorded_warnings:
            warnings.simplefilter("always", ParsingWarning)
            try:
                df = parser.do_parse(rawdata, schema, thing_uuid)
                obs = parser.to_observations(df, source_uri, parser_id)
            except ParsingError as e:
                journal.error(
                    f"Parsing failed. File: {file!r} | Detail: {e}", thing_uuid
                )
                self.set_tags(bucket_name, filename, str(parser_id), "failed", "false")
                raise e
            except Exception as e:
                journal.error(f"Parsing failed. File: {file!r}", thing_uuid)
                self.set_tags(bucket_name, filename, str(parser_id), "failed", "false")
                raise UserInputError("Parsing failed") from e
            for w in recorded_warnings:
                logger.info(f"{w.message!r}")
                journal.warning(f"{w.message}", thing_uuid)

        logger.debug("storing observations to database ...")
        try:
            resp = requests.post(
                f"{self.api_base_url}/observations/upsert/{thing_uuid}",
                json={"observations": obs},
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
        except Exception as e:
            # Tell the user that his parsing was successful
            journal.error(
                f"Parsing was successful, but storing data "
                f"in database failed. File: {file!r}",
                thing_uuid,
            )
            self.set_tags(
                bucket_name, filename, str(parser_id), "db_insert_failed", "false"
            )
            raise e

        if len(obs) > 0:
            # Now everything is fine and we tell the user
            journal.info(
                f"Parsed file: {file!r} | "
                f"Data rows: {df.shape[0]} | "
                f"Stored observations: {len(obs)}",
                thing_uuid,
            )

        self.set_tags(bucket_name, filename, str(parser_id), "successful", "true")
        payload = json.dumps(
            {"thing_uuid": str(thing_uuid), "file": f"{bucket_name}/{filename}"}
        )
        self.mqtt_client.publish(
            topic=self.pub_topic, payload=payload, qos=self.mqtt_qos
        )

    def is_valid_event(self, content: dict):
        logger.debug(f'{content["EventName"]=}')
        return content["EventName"] in (
            "s3:ObjectCreated:Put",
            "s3:ObjectCreated:CompleteMultipartUpload",
        )

    def get_parser_tags(self, bucket_name, filename):
        versions = list(
            self.minio.list_objects(bucket_name, prefix=filename, include_version=True)
        )
        if not versions:
            return None
        versions.sort(key=lambda v: v.last_modified, reverse=True)
        for obj in versions:
            tags = self.minio.get_object_tags(
                bucket_name, filename, version_id=obj.version_id
            )
            if tags and tags["run_successful"] == "true":
                return tags

        return None

    def set_tags(
        self,
        bucket_name,
        filename,
        parser_id,
        parsing_status,
        parsing_successful,
    ):
        # reparsing won't create new object version so we need to overwrite the latest version tags
        try:
            object_tags = self.minio.get_object_tags(bucket_name, filename)
            if object_tags is None:
                object_tags = Tags.new_object_tags()
        except Exception:
            object_tags = Tags.new_object_tags()

        object_tags["parsed_at"] = datetime.now().isoformat()
        object_tags["parser_id"] = parser_id
        object_tags["parsing_status"] = parsing_status
        object_tags["parsing_successful"] = parsing_successful
        self.minio.set_object_tags(bucket_name, filename, object_tags)

    def read_file(self, bucket_name, object_name) -> str:
        stat = self.minio.stat_object(bucket_name, object_name)
        if stat.size > _FILE_MAX_SIZE:
            raise IOError("Maximum filesize of 256M exceeded")
        rawdata = (
            self.minio.get_object(bucket_name, object_name)
            .read()
            .decode()
            # remove the ASCII control character ETX (end-of-text)
            .rstrip("\x03")
        )
        return rawdata


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    ParserJobHandler().run_loop()
