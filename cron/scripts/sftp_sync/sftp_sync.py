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
        return cur.execute(
            "SELECT r.fileserver_uri, r.access_key, r.secret_key, r.bucket "
            "FROM tsm_thing t JOIN tsm_rawdatastorage r ON t.id = r.thing_id "
            "WHERE t.thing_id = %s",
            [thing_id],
        ).fetchone()


def get_external_ftp_credentials(conn, thing_id) -> tuple[str, str, str, str]:
    """Returns (uri, username, password, path)"""
    with conn.cursor() as cur:
        return cur.execute(
            "SELECT ext_sftp_uri, ext_sftp_username, ext_sftp_password, ext_sftp_path "
            "FROM tsm_thing WHERE thing_id = %s",
            [thing_id],
        ).fetchone()


USAGE = """
Usage: sftp_sync.py THING_UUID KEYFILE
Sync external SFTP files to minio storage.

Arguments
  THING_UUID        UUID of the thing.
  KEYFILE           SSH private key file to authenticate at the sftp server.

Additional set the following environment variables:

  MINIO_SECURE      Use minio secure connection; [true, false, 1, 0] 
  FTP_AUTH_DB_DSN   DB which store the credentials for the internal 
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

    for k in ["FTP_AUTH_DB_DSN", "MINIO_SECURE"]:
        if (os.environ.get(k) or None) is None:
            raise EnvironmentError("Environment variable {k} must be set")
    dsn = os.environ["FTP_AUTH_DB_DSN"]
    minio_secure = (  # ensure True as default
        False if os.environ["MINIO_SECURE"].lower() in ["false", "0"] else True
    )

    with psycopg.connect(dsn) as conn:
        ftp_ext = get_external_ftp_credentials(conn, thing_id)
        storage = get_minio_credentials(conn, thing_id)

    if ftp_ext[0] is None:
        raise RuntimeError("Got no external SFTP server from database")
    if storage[0] is None:
        raise RuntimeError("Got no object storage from database")
    target = MinioFS.from_credentials(*storage, secure=minio_secure)
    source = FtpFS.from_credentials(
        *ftp_ext, keyfile_path=ssh_priv_key, missing_host_key_policy=WarningPolicy()
    )
    sync(source, target)
