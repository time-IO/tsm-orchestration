#!/usr/bin/env python3

import click
import logging
import fnmatch

from minio import Minio, S3Error
from minio.commonconfig import Tags

from timeio.feta import FileParser, Thing, ObjectNotFound

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# MR_DATETIME = datetime.datetime(2025, 10, 28, 0, 0, 0, tzinfo=datetime.timezone.utc)


@click.command()
@click.option("--dsn", default="postgresql://postgres:postgres@localhost:5432/postgres")
@click.option("--minio-host", default="localhost:9000")
@click.option("--minio-user", default="minioadmin")
@click.option("--minio-password", default="minioadmin")
@click.option("--minio-secure", default=False)
def main(dsn, minio_host, minio_user, minio_password, minio_secure):
    minio = Minio(
        endpoint=minio_host,
        access_key=minio_user,
        secret_key=minio_password,
        secure=minio_secure,
    )
    for bucket in minio.list_buckets():
        logging.info(f"Processing bucket {bucket.name}")
        try:
            thing = Thing.from_s3_bucket_name(bucket.name, dsn=dsn)
            filename_pattern = thing.s3_store.filename_pattern
        except ObjectNotFound as e:
            logging.warning(e)
            continue
        for v in minio.list_objects(
            bucket.name,
            recursive=True,
            include_version=True,
        ):
            if v.is_delete_marker:
                continue
            if not fnmatch.fnmatch(v.object_name, filename_pattern):
                continue
            try:
                tags = minio.get_object_tags(
                    bucket.name, v.object_name, version_id=v.version_id
                )
            except S3Error as e:
                logging.warning(
                    f"Failed to get tags for {bucket.name}/{v.object_name} (version {v.version_id}): {e}"
                )
                continue

            try:
                if not tags:
                    tags = Tags.new_object_tags()
                if "parser_id" in tags:
                    if tags["parser_id"].isdigit():
                        parser = FileParser.from_id(tags["parser_id"], dsn)
                    else:
                        continue
                else:
                    parser = thing.s3_store.file_parser

                tags["parser_id"] = str(parser.uuid)
                minio.set_object_tags(
                    bucket.name, v.object_name, tags, version_id=v.version_id
                )

                logging.info(
                    f"Set 'parser_id' tag for {bucket.name}/{v.object_name} (version {v.version_id}) to {parser.uuid}"
                )

            except Exception:
                logging.exception(
                    f"Failed to update tags for {bucket.name}/{v.object_name} (version {v.version_id})"
                )
                continue


if __name__ == "__main__":
    main()
