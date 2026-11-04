from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatch

import paho.mqtt.client as mqtt
from minio import Minio, S3Error

from timeio.feta import FileParser, ObjectNotFound, Thing
from timeio.journaling import Journal

logger = logging.getLogger("reparse")

TOPIC = "object_storage_notification_triggered"


@dataclass
class ReparseSummary:
    published: int = 0
    skipped: int = 0
    failed: int = 0


def make_publisher(
    host: str,
    username: str,
    password: str,
    client_id: str,
) -> mqtt.Client:
    """Own MQTT client with its own network thread, used only to send messages."""
    host, port = host.split(":")
    port = int(port)

    client = mqtt.Client(client_id=client_id, clean_session=False)
    client.enable_logger(logger)
    client.username_pw_set(username=username, password=password)
    if port == 8883:
        client.tls_set()
    client.suppress_exceptions = False
    client.connect(host, port, keepalive=60)
    client.loop_start()
    return client


def parser_exists(uuid: str, dsn: str) -> bool:
    try:
        FileParser.from_uuid(uuid, dsn=dsn)
    except ObjectNotFound:
        return False
    return True


def get_parse_info(minio: Minio, bucket: str, fname: str) -> tuple[bool, str | None]:
    """Read-only: (parsed successfully?, parser uuid from the tag) of the latest object version"""
    try:
        tags = minio.get_object_tags(bucket, fname)
    except S3Error:
        return False, None
    if not tags or tags.get("parsing_status") != "successful":
        return False, None
    return True, tags.get("parser_id")


def _to_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def reparse_files(
    thing: Thing,
    minio: Minio,
    publisher: mqtt.Client,
    journal: Journal,
    dsn: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    filename_pattern: str | None = None,
    parser_uuid: str | None = None,
    include_parsed: bool = False,
    parsed_files_parser: str = "current",
) -> ReparseSummary:
    store = thing.raw_data_storage
    bucket = store.bucket
    start, end = _to_utc(start_date), _to_utc(end_date)
    current_parser_uuid = str(thing.s3_store.file_parser.uuid)
    parser_cache: dict[str, bool] = {}
    summary = ReparseSummary()

    for obj in minio.list_objects(bucket):
        fname = obj.object_name
        if not fnmatch(fname, store.filename_pattern):
            continue
        if filename_pattern and not fnmatch(fname, filename_pattern):
            continue
        if start and obj.last_modified < start:
            continue
        if end and obj.last_modified > end:
            continue

        parsed, original_uuid = get_parse_info(minio, bucket, fname)
        if parsed and not include_parsed:
            logger.debug(f"skipping already parsed file: {fname}")
            continue

        if parser_uuid:  # explicitly chosen
            chosen = parser_uuid
        elif parsed and parsed_files_parser == "original":
            chosen = original_uuid
            if chosen not in parser_cache:
                parser_cache[chosen] = bool(chosen) and parser_exists(chosen, dsn)
            if not parser_cache[chosen]:
                msg = (
                    f"File {fname!r} not reparsed: the parser it was originally "
                    f"parsed with ({chosen}) no longer exists."
                )
                logger.warning(msg)
                journal.warning(msg, thing.uuid)
                summary.skipped += 1
                continue
        else:
            chosen = current_parser_uuid

        message = {
            "EventName": "s3:ObjectCreated:Put",
            "reparsing": True,
            "parser_uuid": chosen,
            "Key": f"{bucket}/{fname}",
        }
        logger.info(f"republishing file: {message['Key']}")
        result = publisher.publish(TOPIC, json.dumps(message), qos=1)
        if result[0] != 0:
            summary.failed += 1
            logger.warning(f"Failed to send reprocessing message for {message['Key']}")
        else:
            summary.published += 1
            result.wait_for_publish()
    text = (
        f"Reparsing finished: {summary.published} file(s) sent for reparsing, "
        f"{summary.skipped} skipped, {summary.failed} failed to send."
    )
    logger.info(text)
    journal.info(text, thing.uuid)
    return summary
