#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
from fnmatch import fnmatch

import click
from datetime import datetime, timezone
from minio import Minio, S3Error
import paho.mqtt.client as mqtt

from timeio.feta import Thing, FileParser, ObjectNotFound
from timeio.journaling import Journal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reprocess-files")
journal = Journal("Reprocessing", errors="warn")


def setupMQTT(host, username, password):
    host, port = host.split(":")
    port = int(port)

    client = mqtt.Client(client_id="reparse-files", clean_session=False)
    client.enable_logger(logger)

    client.username_pw_set(username, password)

    if port == 8883:
        client.tls_set()
        # client.tls_insecure_set(True)

    client.suppress_exceptions = False
    client.connect(host, port, keepalive=60)

    return client


def get_parse_info(minio, bucket, fname) -> tuple[bool, str | None]:
    """Read-only: (parsed successfully?, parser uuid from the tag) of the latest
    object version."""
    try:
        tags = minio.get_object_tags(bucket, fname)
    except S3Error:
        return False, None
    if not tags or tags.get("parsing_status") != "successful":
        return False, None
    return True, tags.get("parser_id")


def parser_exists(uuid, dsn) -> bool:
    try:
        FileParser.from_uuid(uuid, dsn=dsn)
    except ObjectNotFound:
        return False
    return True


@click.command()
@click.option(
    "--dsmdb-dsn",
    default="postgresql://dsm_db:dsm_db@localhost:5432/postgres",
    envvar="DSMDB_DSN",
)
@click.option(
    "--thing-uuid", default="0a308373-ab29-4317-b351-1443e8a1babd", envvar="THING_UUID"
)
@click.option("--minio-host", default="localhost:9000", envvar="MINIO_HOST")
@click.option("--minio-user", default="minioadmin", envvar="MINIO_USER")
@click.option("--minio-password", default="minioadmin", envvar="MINIO_PASSWORD")
@click.option("--mqtt-host", default="localhost:1883", envvar="MQTT_HOST")
@click.option("--mqtt-user", default="mqtt", envvar="MQTT_USER")
@click.option("--mqtt-password", default="mqtt", envvar="MQTT_PASSWORD")
@click.option("--filename-pattern", default=None)
@click.option("--start-date", default=None)
@click.option("--end-date", default=None)
@click.option(
    "--parser",
    "parser_uuid",
    default=None,
    help="UUID of the parser to use. Defaults to the current parser of the thing.",
)
@click.option(
    "--include-parsed",
    is_flag=True,
    default=False,
    help="Also reparse files that are already parsed successfully. "
    "By default only files not parsed successfully are reparsed.",
)
@click.option(
    "--parsed-files-parser",
    type=click.Choice(["current", "original"]),
    default="current",
    help="Parser for files that are already parsed (need --include-parsed): "
    "the current parser of the thing, or the one they were originally parsed with.",
)
def main(
    dsmdb_dsn,
    thing_uuid,
    minio_host,
    minio_user,
    minio_password,
    mqtt_host,
    mqtt_user,
    mqtt_password,
    filename_pattern,
    start_date,
    end_date,
    parser_uuid,
    include_parsed,
    parsed_files_parser,
):
    thing = Thing.from_uuid(thing_uuid, dsn=dsmdb_dsn)
    store = thing.raw_data_storage
    bucket = store.bucket

    minio = Minio(
        endpoint=minio_host,
        access_key=minio_user,
        secret_key=minio_password,
        secure=not minio_host.startswith("localhost"),
    )

    current_parser_uuid = str(thing.s3_store.file_parser.uuid)
    parser_cache: dict[str, bool] = {}
    found = published = failed = skipped = 0
    if parser_uuid and not parser_exists(parser_uuid, dsmdb_dsn):
        raise click.BadParameter(
            f"parser {parser_uuid!r} not found", param_hint="--parser"
        )

    mqtt = setupMQTT(mqtt_host, mqtt_user, mqtt_password)

    fnpattern_from_thing = store.filename_pattern
    fnpattern_from_job = filename_pattern
    if start_date:
        start = datetime.fromisoformat(start_date)
        start = start if start.tzinfo else start.replace(tzinfo=timezone.utc)
    if end_date:
        end = datetime.fromisoformat(end_date)
        end = end if end.tzinfo else end.replace(tzinfo=timezone.utc)

    mqtt.loop_start()

    message = {"EventName": "s3:ObjectCreated:Put", "reparsing": True}
    if parser_uuid:
        message["parser_uuid"] = parser_uuid
    for obj in minio.list_objects(bucket):
        fname = obj.object_name
        fdate = obj.last_modified
        if fnmatch(fname, fnpattern_from_thing):
            cond2 = not fnpattern_from_job or fnmatch(fname, fnpattern_from_job)
            cond3 = True if not start_date else fdate >= start
            cond4 = True if not end_date else fdate <= end
            if cond2 and cond3 and cond4:
                parsed, original_uuid = get_parse_info(minio, bucket, fname)
                if parsed and not include_parsed:
                    logger.debug(f"skipping already parsed file: {fname}")
                    continue

                if parser_uuid:  # explicit chosen
                    chosen = parser_uuid
                elif parsed and parsed_files_parser == "original":
                    chosen = original_uuid
                    if chosen not in parser_cache:
                        parser_cache[chosen] = bool(chosen) and parser_exists(
                            chosen, dsmdb_dsn
                        )
                    if not parser_cache[chosen]:
                        msg = (
                            f"File {fname!r} not reparsed: the parser it was originally "
                            f"parsed with ({chosen}) no longer exists."
                        )
                        logger.warning(msg)
                        journal.warning(msg, thing.uuid)
                        skipped += 1
                        continue
                else:
                    chosen = current_parser_uuid

                found += 1
                message["parser_uuid"] = chosen
                message["Key"] = f"{bucket}/{fname}"
                logging.info(f"republishing file: {message['Key']}")
                result = mqtt.publish(
                    topic="object_storage_notification_triggered",
                    payload=json.dumps(message),
                    qos=1,
                )
                if result[0] != 0:
                    failed += 1
                    logger.warning(
                        f"Failed to deliver reprocessing message for file: {message['Key']}"
                    )
                else:
                    published += 1
                    result.wait_for_publish()

    summary = (
        f"Reparsing finished: {published} file(s) sent for reparsing, "
        f"{skipped} skipped, {failed} failed to send."
    )
    logger.info(summary)
    journal.info(summary, thing.uuid)
    mqtt.loop_stop()
    mqtt.disconnect()


if __name__ == "__main__":
    main()
