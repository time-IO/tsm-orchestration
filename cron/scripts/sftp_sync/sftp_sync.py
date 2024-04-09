#!/usr/bin/env python
from __future__ import annotations

import os
import sys
import psycopg
import logging
from remote_fs import MinioFS, FtpFS, RemoteFS
from paramiko import WarningPolicy

logger = logging.getLogger(__name__)


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


def sync(src: RemoteFS, trg: RemoteFS):

    for path in src.files:
        logger.info(f"SYNCING: {path}")

        # dirs
        if src.is_dir(path):
            if not trg.exist(path):
                trg.mkdir(path)
            continue

        # regular files
        if (
            not trg.exist(path)
            or src.size(path) != trg.size(path)
            or src.last_modified(path) > trg.last_modified(path)
        ):
            trg.update(src, path)
            continue


if __name__ == "__main__":

    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    if len(sys.argv) != 2:
        raise ValueError("Expected a thing_id as first and only argument.")
    thing_id = sys.argv[1]

    for k in ["SSH_PRIV_KEY_PATH", "FTP_AUTH_DB_URI", "MINIO_SECURE"]:
        if (os.environ.get(k) or None) is None:
            raise EnvironmentError("Environment variable {k} must be set")
    ssh_priv_key = os.path.join(os.environ["SSH_KEYFILE_DIR"], f"{thing_id}")
    dsn = os.environ["FTP_AUTH_DB_DSN"]
    minio_secure = (  # ensure True as default
        False if os.environ["MINIO_SECURE"].lower() in ["false", "0"] else True
    )

    with psycopg.connect(dsn) as conn:
        ftp_ext = get_external_ftp_credentials(conn, thing_id)
        ftp_int = get_minio_credentials(conn, thing_id)

    target = MinioFS.from_credentials(*ftp_int, secure=minio_secure)
    source = FtpFS.from_credentials(
        *ftp_ext, keyfile_path=ssh_priv_key, missing_host_key_policy=WarningPolicy()
    )
    sync(source, target)
