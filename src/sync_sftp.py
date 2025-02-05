#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import psycopg
import logging

from paramiko import WarningPolicy
from timeio.crypto import decrypt
from timeio.remote_fs import MinioFS, FtpFS, sync


def get_minio_bucket_name(conn, thing_id) -> str:
    """Returns bucket_name from configdb."""
    with conn.cursor() as cur:
        res = cur.execute(
            "select s3.bucket from config_db.s3_store s3 "
            "join config_db.thing t on s3.id = t.s3_store_id "
            "where t.uuid = %s",
            [thing_id],
        ).fetchone()
        if res is None or not res[0]:
            raise RuntimeError(f"No S3 bucket found for thing {thing_id!r}")
        return res[0]


def get_external_ftp_credentials(conn, thing_id) -> tuple[str, str, str, str]:
    """Returns (uri, username, password, path)"""
    with conn.cursor() as cur:
        res = cur.execute(
            'select ftp.uri, ftp."user", ftp.password, ftp.path '
            "from config_db.ext_sftp ftp join config_db.thing t "
            "on ftp.id = t.ext_sftp_id "
            "where t.uuid = %s",
            [thing_id],
        ).fetchone()
        if res is None or res[0] in ["", None] or res[1] in ["", None]:
            raise RuntimeError(f"No Ext-sFTP credentials found for thing {thing_id!r}")
        res_list = list(res)
        res_list[2] = decrypt(res_list[2])
        return tuple(res_list)


USAGE = """
Usage: sftp_sync.py THING_UUID KEYFILE
Sync external SFTP files to minio storage.

Arguments
  THING_UUID        UUID of the thing.
  KEYFILE           SSH private key file to authenticate at the sftp server.

Additional set the following nvironment variables:

  MINIO_URL         Minio URL to sync to.
  MINIO_USER        Minio user with r/w privileges 
  MINIO_PASSWORD    Password for minio user above.
  MINIO_SECURE      Use minio secure connection; [true, false, 1, 0] 
  CONFIGDB_DSN      DB which stores the credentials for the external sftp server 
                    (source of sync) and also the (existing) bucket-name for the 
                    target S3 storage. See also DSN format below. 
  LOG_LEVEL         Set the verbosity, defaults to INFO.
                    [DEBUG, INFO, WARNING, ERROR, CRITICAL]

DSN format: 
  postgresql://[user[:password]@][netloc][:port][/dbname]
"""

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(USAGE)
        exit(1)

    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())
    thing_id = sys.argv[1]
    ssh_priv_key = sys.argv[2]

    for k in [
        "CONFIGDB_DSN",
        "MINIO_URL",
        "MINIO_USER",
        "MINIO_PASSWORD",
        "MINIO_SECURE",
    ]:
        if not os.environ.get(k):
            raise EnvironmentError(f"Environment variable {k} must be set")
    dsn = os.environ["CONFIGDB_DSN"]
    minio_secure = (  # ensure True as default
        False if os.environ["MINIO_SECURE"].lower() in ["false", "0"] else True
    )

    logging.getLogger("sftp_sync").info("Thing UUID: %s", thing_id)

    with psycopg.connect(dsn) as conn:
        ftp_ext = get_external_ftp_credentials(conn, thing_id)
        bucket = get_minio_bucket_name(conn, thing_id)

    target = MinioFS.from_credentials(
        endpoint=os.environ["MINIO_URL"],
        access_key=os.environ["MINIO_USER"],
        secret_key=os.environ["MINIO_PASSWORD"],
        bucket_name=bucket,
        secure=minio_secure,
    )
    source = FtpFS.from_credentials(
        *ftp_ext, keyfile_path=ssh_priv_key, missing_host_key_policy=WarningPolicy()
    )
    sync(source, target)
