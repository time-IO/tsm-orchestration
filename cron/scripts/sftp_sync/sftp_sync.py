#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import psycopg
import logging
from remote_fs import MinioFS, FtpFS, sync
from paramiko import WarningPolicy


def get_minio_credentials(conn, thing_id) -> tuple[str, str, str, str]:
    """Returns (uri, access_key, secret_key, bucket_name)"""
    with conn.cursor() as cur:
        res = cur.execute(
            "SELECT r.access_key, r.secret_key, r.bucket "
            "FROM tsm_thing t JOIN tsm_rawdatastorage r ON t.id = r.thing_id "
            "WHERE t.thing_id = %s",
            [thing_id],
        ).fetchone()
        if res is None or not res[0]:
            raise RuntimeError(
                "No object storage credentials found in frontend database"
            )
        a, s, b = res
        return os.environ["MINIO_URL"], a, s, b


def get_external_ftp_credentials(conn, thing_id) -> tuple[str, str, str, str]:
    """Returns (uri, username, password, path)"""
    with conn.cursor() as cur:
        res = cur.execute(
            "SELECT ext_sftp_uri, ext_sftp_username, ext_sftp_password, ext_sftp_path "
            "FROM tsm_thing WHERE thing_id = %s",
            [thing_id],
        ).fetchone()
        if res is None or res[0] in ["", None] or res[1] in ["", None]:
            raise RuntimeError(
                "No external sftp credentials present in frontend database"
            )
        return res


USAGE = """
Usage: sftp_sync.py THING_UUID KEYFILE
Sync external SFTP files to minio storage.

Arguments
  THING_UUID        UUID of the thing.
  KEYFILE           SSH private key file to authenticate at the sftp server.

Additional set the following environment variables:

  MINIO_SECURE      Use minio secure connection; [true, false, 1, 0] 
  CONFIGDB_DSN      DB which store the credentials for the internal 
                    and external sftp server. See also DSN format below. 
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

    for k in ["CONFIGDB_DSN", "MINIO_URL", "MINIO_SECURE"]:
        if not os.environ.get(k):
            raise EnvironmentError(f"Environment variable {k} must be set")
    dsn = os.environ["CONFIGDB_DSN"]
    minio_secure = (  # ensure True as default
        False if os.environ["MINIO_SECURE"].lower() in ["false", "0"] else True
    )

    logging.getLogger("sftp_sync").info("Thing UUID: %s", thing_id)

    with psycopg.connect(dsn) as conn:
        ftp_ext = get_external_ftp_credentials(conn, thing_id)
        storage = get_minio_credentials(conn, thing_id)

    target = MinioFS.from_credentials(*storage, secure=minio_secure)
    source = FtpFS.from_credentials(
        *ftp_ext, keyfile_path=ssh_priv_key, missing_host_key_policy=WarningPolicy()
    )
    sync(source, target)
