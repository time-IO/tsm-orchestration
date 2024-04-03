#!/usr/bin/env python
from __future__ import annotations

import os
from os.path import basename
import sys
import stat
import warnings
from dataclasses import dataclass

import psycopg
from paramiko import SSHClient, WarningPolicy, SFTPClient
import logging

logger = logging.getLogger(__name__)


@dataclass
class FtpMeta:
    uri: str
    username: str
    sync_dir: str | None
    password: str | None = None
    keyfile_path: str = None


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


def sync(src: SFTPClient, dest: SFTPClient):

    def update_file(path, src_attr) -> None:
        with src.open(path, "rb") as fl:
            dest.putfo(fl, path)
            dest.utime(path, (src_attr.st_atime, src_attr.st_atime))

    def sync_file(path, src_attr) -> None:
        logger.info(f"syncing FILE {path}")
        try:
            dest_attr = dest.lstat(path)
        except FileNotFoundError:
            update_file(path, src_attr)
            return

        if (
            dest_attr.st_size == src_attr.st_size
            and dest_attr.st_mtime == src_attr.st_mtime
        ):
            return
        update_file(path, src_attr)

    def sync_dir(path) -> None:
        logger.info(f"syncing DIR  {path}")
        for filename in src.listdir(path):
            filepath = f"{path}/{filename}"
            src_attr = src.lstat(filepath)

            # src is a regular file
            if stat.S_ISREG(src_attr.st_mode):
                sync_file(filepath, src_attr)
                continue
            # src is not a directory
            if not stat.S_ISDIR(src_attr.st_mode):
                warnings.warn(
                    "Only regular files and dirs "
                    "are supported for syncing"
                )  # fmt: skip
                continue
            # src is a directory, dest might not exist or
            # might be a regular file
            try:
                dest_attr = dest.lstat(filepath)
                if not stat.S_ISDIR(dest_attr.st_mode):
                    dest.remove(filepath)
            except FileNotFoundError:
                dest.mkdir(filepath)
            # src is a directory, dest is a directory
            # so we recurse
            sync_dir(filepath)

    sync_dir(".")


def test():
    ftp1 = connect_ftp(
        FtpMeta(
            uri="tsm.intranet.ufz.de",
            sync_dir="ftp_test",
            username="bpalm",
            password=None,
            keyfile_path=os.environ.get("TEST_KEYFILE_PATH"),
        )
    )
    ftp2 = connect_ftp(
        FtpMeta(
            uri="tsm.ufz.de",
            sync_dir="fooo",
            username="bpalm",
            password=None,
            keyfile_path=os.environ.get("TEST_KEYFILE_PATH"),
        )
    )
    sync(ftp1, ftp2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test()

    exit(1)
    if len(sys.argv) != 2:
        raise ValueError("Expected a thing_id as first and only argument.")
    thing_id = sys.argv[1]

    for k in ["SSH_PRIV_KEY_PATH", "FTP_AUTH_DB_URI"]:
        if (os.environ.get(k) or None) is None:
            raise EnvironmentError("Environment variable {k} must be set")
    with psycopg.connect(os.environ["FTP_AUTH_DB_DSN"]) as conn:
        ftp_ext = get_external_ftp(conn, thing_id)
        ftp_int = get_internal_ftp(conn, thing_id)

    src = connect_ftp(ftp_ext)
    dest = connect_ftp(ftp_int)
    sync(src, dest)
