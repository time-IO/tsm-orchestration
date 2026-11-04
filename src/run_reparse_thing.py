#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import click
from minio import Minio

from timeio.feta import Thing
from timeio.journaling import Journal
from timeio.reparse import make_publisher, parser_exists, reparse_files

logging.basicConfig(level=logging.INFO)
journal = Journal("Reprocessing", errors="warn")


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

    minio = Minio(
        endpoint=minio_host,
        access_key=minio_user,
        secret_key=minio_password,
        secure=not minio_host.startswith("localhost"),
    )

    if parser_uuid and not parser_exists(parser_uuid, dsmdb_dsn):
        raise click.BadParameter(
            f"parser {parser_uuid!r} not found", param_hint="--parser"
        )
    publisher = make_publisher(mqtt_host, mqtt_user, mqtt_password, "reparse-files-cli")
    try:
        reparse_files(
            thing,
            minio,
            publisher,
            journal,
            dsmdb_dsn,
            start_date=start_date,
            end_date=end_date,
            filename_pattern=filename_pattern,
            parser_uuid=parser_uuid,
            include_parsed=include_parsed,
            parsed_files_parser=parsed_files_parser,
        )
    finally:
        publisher.loop_stop()
        publisher.disconnect()


if __name__ == "__main__":
    main()
