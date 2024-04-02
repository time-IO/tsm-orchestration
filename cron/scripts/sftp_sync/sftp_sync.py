#!/usr/bin/env python
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import psycopg
from paramiko import SSHClient, WarningPolicy, SFTPClient


@dataclass
class FtpMeta:
    uri: str
    username: str
    sync_dir: str | None
    password: str | None = None
    keyfile_path: str = None


class Test:
    @staticmethod
    def get_external_ftp(conn, thing_id) -> FtpMeta:
        return FtpMeta(
            uri="tsm.intranet.ufz.de",
            sync_dir="ftp_test",
            username="bpalm",
            password=None,
            keyfile_path=os.environ.get("TEST_KEYFILE_PATH"),
        )


def get_internal_ftp(conn, thing_id) -> FtpMeta:
    with conn.cursor() as cur:
        values = cur.execute(
            "SELECT r.fileserver_uri, r.bucket, r.access_key, r.secret_key "
            "FROM tsm_thing t JOIN tsm_rawdatastorage r ON t.id = r.thing_id "
            "WHERE t.thing_id = %s",
            [thing_id],
        ).fetchone()
    return FtpMeta(*values)


def get_external_ftp(conn, thing_id) -> FtpMeta:
    with conn.cursor() as cur:
        values = cur.execute(
            "SELECT ext_sftp_uri, ext_sftp_path, ext_sftp_username, ext_sftp_password "
            "FROM tsm_thing WHERE thing_id = %s",
            [thing_id],
        ).fetchone()
    ftp = FtpMeta(*values)
    ftp.keyfile_path = os.path.join(os.environ["SSH_KEYFILE_DIR"], f"{thing_id}")
    return ftp


def connect_ftp(ftp: FtpMeta) -> SFTPClient:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(WarningPolicy)
    ssh.connect(
        hostname=ftp.uri,
        username=ftp.username,
        password=ftp.password or None,
        key_filename=ftp.keyfile_path or None,
        look_for_keys=False,
        compress=True,
    )
    sftp = ssh.open_sftp()
    # might raise FileNotFoundError,
    # but that is good enough
    if ftp.sync_dir and sftp:
        sftp.chdir(ftp.sync_dir)
    return sftp


def sync(source: SFTPClient, target: SFTPClient):
    # get remote file list
    # get our file list
    # files = new files
    # compare other files by dates
    # files += newer (by date) files
    # for f in files:
    #  download file (theirs)
    #  upload file (ours)
    pass


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Expected a thing_id as first and only argument.")
    thing_id = sys.argv[1]

    for k in ["SSH_PRIV_KEY_PATH", "FTP_AUTH_DB_URI"]:
        if (os.environ.get(k) or None) is None:
            raise EnvironmentError("Environment variable {k} must be set")
    with psycopg.connect(os.environ["FTP_AUTH_DB_DSN"]) as conn:
        ftp_int = get_internal_ftp(conn, thing_id)
        ftp_ext = get_external_ftp(conn, thing_id)

    source = connect_ftp(ftp_ext)
    target = connect_ftp(ftp_int)
    sync(source, target)
