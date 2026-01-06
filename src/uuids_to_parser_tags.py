#!/usr/bin/env python3

import click
import logging
import fnmatch
import datetime

from minio import Minio, S3Error
from timeio.feta import FileParser, Thing, ObjectNotFound

# MR_DATETIME = datetime.datetime(2025, 10, 28, 0, 0, 0, tzinfo=datetime.timezone.utc)


@click.command()
# @click.option("--dsn", default="postgresql://postgres:postgres@localhost:5432/postgres")
@click.option(
    "--dsn",
    default="postgresql://rdm_tsm_adm:7KX[3ocaCoU2!h0NNwH]]Gc8K<3F>odG@postgres.intranet.ufz.de/rdm_tsm",
)
@click.option("--minio-host", default="localhost:9000")
@click.option("--minio-user", default="minioadmin")
@click.option("--minio-password", default="minioadmin")
def main(dsn, minio_host, minio_user, minio_password):
    minio = Minio(
        endpoint=minio_host,
        access_key=minio_user,
        secret_key=minio_password,
        secure=not minio_host.startswith("localhost"),
    )
    for bucket in minio.list_buckets():
        logging.info(f"Processing bucket {bucket.name}")
        try:
            thing = Thing.from_s3_bucket_name(bucket.name, dsn=dsn)
            filename_pattern = thing.s3_store.filename_pattern
        except ObjectNotFound as e:
            logging.warning(e)
            continue
        versions = minio.list_objects(
            bucket.name,
            recursive=True,
            include_version=True,
        )
        for v in versions:
            if v.is_delete_marker:
                continue
            if not fnmatch.fnmatch(v.object_name, filename_pattern):
                continue
            try:
                tags = minio.get_object_tags(
                    bucket.name, v.object_name, version_id=v.version_id
                )
            except S3Error as e:
                logging.warning(e)
                continue
            if tags and "parser_id" in tags:
                try:
                    parser = FileParser.from_id(tags["parser_id"], dsn)
                    if tags["parser_id"] == str(parser.uuid):
                        continue
                    tags["parser_id"] = str(parser.uuid)
                    minio.set_object_tags(
                        bucket.name, v.object_name, tags, version_id=v.version_id
                    )
                    logging.info(
                        f"Set 'parser_id' tag for {bucket.name}/{v.object_name} with version '{v.version_id}' to '{parser.uuid}'"
                    )
                except Exception as e:
                    logging.warning(e)
                    continue


if __name__ == "__main__":
    main()
