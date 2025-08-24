#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import click
import minio
import psycopg
from crontab import CronTab
from minio.credentials import StaticProvider


# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s | %(name)s] %(levelname)s: %(message)s"
)


def delete_bucket(minio_host, minio_user, minio_password, minio_bucket):

    client = minio.Minio(
        minio_host,
        access_key=minio_user,
        secret_key=minio_password,
        secure=not minio_host.startswith("localhost"),
    )

    admin_client = minio.MinioAdmin(
        endpoint=minio_host,
        credentials=StaticProvider(minio_user, minio_password),
        secure=not minio_host.startswith("localhost"),
    )

    if not client.bucket_exists(minio_bucket):
        return

    # 1. Clear the bucket
    objects = client.list_objects(minio_bucket, recursive=True, include_version=True)

    for obj in objects:
        client.remove_object(minio_bucket, obj.object_name, version_id=obj.version_id)

    # 2. Remove the bucket
    client.remove_bucket(minio_bucket)

    # 3. Remove user
    admin_client.user_remove(minio_bucket)


def delete_thing_entry(cursor, thing_uuid):
    cursor.execute(
        "DELETE FROM config_db.thing where uuid = %s RETURNING project_id", [thing_uuid]
    )
    cursor.execute(
        """
        SELECT schema from config_db.database d
        JOIN config_db.project p on p.database_id = d.id
        WHERE p.id = %s
        """,
        cursor.fetchone(),
    )
    schema = cursor.fetchall()[0][0]
    return schema


def delete_mqtt_user(cursor, thing_uuid):
    cursor.execute(
        """
        DELETE FROM mqtt_aut.mqtt_user
        WHERE thing_uuid  = %s
        """,
        thing_uuid,
    )


def delete_s3store_entry(cursor, id):
    cursor.execute(
        """
        DELETE FROM config_db.s3_store where id = %s
        RETURNING bucket
        """,
        [id],
    )
    return cursor.fetchall()[0][0]


def delete_mqtt_entry(cursor, id):
    cursor.execute("DELETE FROM config_db.mqtt where id = %s", [id])


def delete_ext_sftp_entry(cursor, id):
    cursor.execute("DELETE FROM config_db.ext_sftp where id = %s", [id])


def delete_ext_api_entry(cursor, id):
    cursor.execute("DELETE FROM config_db.ext_api where id = %s", [id])


def delete_crontab_entry(crontab_file, thing_uuid):
    cron = CronTab(tabfile=crontab_file, user=False)
    for job in cron:
        if thing_uuid in job.command:
            cron.remove(job)
    cron.write()


def delete_legacy_qc(cursor, id):
    cursor.execute("DELETE FROM config_db.qaqc_test where qaqc_id = %s", [id])
    cursor.execute("DELETE FROM config_db.qaqc where id = %s", [id])


def delete_qc(cursor, sta_datastream_ids):
    query = """
    DELETE FROM config_db.qaqc_test
    WHERE jsonb_path_exists(streams, '$[*] ? (@.sta_stream_id in %s)')
    RETURNING qaqc_id
    """
    cursor.execute(query, sta_datastream_ids)
    ids = cursor.fetchall()
    for id in ids:
        query = f"""
        DELETE FROM qaqc
        WHERE {id} NOT IN (
            SELECT DISTINCT qaqc_id
            FROM qaqc_function
        )
        """
        cursor.execute(query)


def delete_thing_from_schema(cur, schema, thing_uuid):
    """
    NOTE:
    We don't delete from related_datasteam and relation_role, as this fields are not really used yet.
    """
    cur.execute(
        f"""
        SELECT d.id from {schema}.datastream d
            JOIN {schema}.thing t ON t.id=d.thing_id
        WHERE t.uuid = %s
        """,
        (thing_uuid,),
    )
    datastream_ids = [str(i[0]) for i in cur.fetchall()]
    if datastream_ids:
        cur.execute(
            f"""
            DELETE FROM {schema}.observation WHERE datastream_id in ({",". join(datastream_ids)})
            """
        )
        cur.execute(
            f"""
            DELETE FROM {schema}.datastream WHERE id in ({",". join(datastream_ids)});
            """
        )

    cur.execute(
        f"""
        DELETE FROM {schema}.journal
        WHERE thing_id = (
            SELECT id FROM {schema}.thing WHERE uuid = %s
        )
        """,
        (thing_uuid,),
    )
    cur.execute(
        f"""
        DELETE FROM {schema}.thing WHERE uuid = %s
        """,
        (thing_uuid,),
    )


def get_ids(cursor, thing_uuid):
    cursor.execute(
        "select s3_store_id, mqtt_id, ext_sftp_id, ext_api_id, legacy_qaqc_id from config_db.thing where uuid = %s",
        [thing_uuid],
    )
    ids = cursor.fetchone()
    if ids is None:
        raise ValueError(f"No such thing '{thing_uuid}'!")

    cursor.execute(
        """SELECT device_property_id FROM sms_datastream_link where thing_id = %s;""",
        [thing_uuid],
    )
    return ids + ([row[0] for row in cursor.fetchall()],)


@click.command()
@click.option("--thing-uuid", required=True)
@click.option(
    "--dsn",
    default="postgresql://postgres:postgres@localhost:5432/postgres",
    envvar="POSTGRES_DSN",
)
@click.option("--minio-host", default="localhost:9000", envvar="OBJECT_STORAGE_HOST")
@click.option("--minio-user", default="minioadmin", envvar="OBJECT_STORAGE_ROOT_USER")
@click.option(
    "--minio-password", default="minioadmin", envvar="OBJECT_STORAGE_ROOT_PASWORD"
)
@click.option("--crontab-file", required=True)
def main(thing_uuid, dsn, minio_host, minio_user, minio_password, crontab_file):
    """
    * Deletes the given thing, related datastreams and observations from `obervationdb`
    * Deletes from configdb:
      - given thing and related entries in ext_api, ext_sftp, mqtt, qaqc, qaqc_test, s3_store
      - mqtt user
      - minio bucket and user -> NOTE: This is because of WORM protection not working right now
      - crontab entries
    """

    logger = logging.getLogger("DELETE THING")
    logger.info(
        f"Deleting '{thing_uuid}' from database '{dsn}' and object-storage '{minio_host}'"
    )

    conn = psycopg.connect(dsn)
    conn.autocommit = False
    with conn.cursor() as cur:

        (
            s3_store_id,
            mqtt_id,
            ext_sftp_id,
            ext_api_id,
            legacy_qaqc_id,
            sta_datastream_ids,
        ) = get_ids(cur, thing_uuid)

        schema = delete_thing_entry(cur, thing_uuid)

        if s3_store_id:
            minio_bucket = delete_s3store_entry(cur, s3_store_id)
            try:
                delete_bucket(
                    minio_host=minio_host,
                    minio_user=minio_user,
                    minio_password=minio_password,
                    minio_bucket=minio_bucket,
                )
            except minio.error.S3Error:
                logger.warning(f"Unable to delete minio bucket: '{minio_bucket}")

        if mqtt_id:
            delete_mqtt_entry(cur, mqtt_id)

        if ext_sftp_id:
            delete_ext_sftp_entry(cur, ext_sftp_id)

        if ext_api_id:
            delete_ext_api_entry(cur, ext_api_id)
            delete_crontab_entry(crontab_file, thing_uuid)

        if legacy_qaqc_id:
            delete_legacy_qc(cur, legacy_qaqc_id)

        if sta_datastream_ids:
            delete_qc(cur, sta_datastream_ids)
            logger.warning(
                "There are SMS datastream links which need to be deleted manually from the SMS"
            )

        delete_thing_from_schema(cur, schema, thing_uuid)
        cur.close()
    conn.commit()


if __name__ == "__main__":
    main()
