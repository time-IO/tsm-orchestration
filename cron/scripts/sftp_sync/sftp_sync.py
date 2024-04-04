#!/usr/bin/env python
from __future__ import annotations

import os
import stat
from dataclasses import dataclass

from paramiko import SSHClient, WarningPolicy, SFTPClient, SFTPAttributes
import logging

logger = logging.getLogger(__name__)


@dataclass
class FtpMeta:
    uri: str
    username: str
    sync_dir: str | None = None
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
    host, *port = ftp.uri.split(":")
    port = port[0] if port else 22
    ssh.connect(
        hostname=host,
        port=port,
        username=ftp.username,
        password=ftp.password or None,
        key_filename=ftp.keyfile_path or None,
        look_for_keys=False,  # todo maybe ?
        allow_agent=False,
        compress=True,
    )
    sftp = ssh.open_sftp()
    if ftp.sync_dir:
        # might raise FileNotFoundError,
        # but that is good enough
        sftp.chdir(ftp.sync_dir)
    return sftp


def get_files(sftp, path) -> dict:
    # Note that directories always appear
    # before any files from that directory
    # appear.
    files = {}
    dirs = []
    # we must avoid calling listdir_iter multiple
    # times, otherwise it might cause a deadlock.
    # That's why we do not recurse within the loop.
    for attrs in sftp.listdir_iter(path):
        file_path = f"{path}/{attrs.filename}"
        if stat.S_ISDIR(attrs.st_mode):
            dirs.append(file_path)
        files[file_path] = attrs
    for dir_ in dirs:
        files.update(get_files(sftp, dir_))
    return files


def sync(src: SFTPClient, dest: SFTPClient):

    def is_dir(attrs: SFTPAttributes) -> bool:
        return stat.S_ISDIR(attrs.st_mode)

    def mk_dir(path) -> None:
        # force creation of a dir.
        # delete file with same name
        # if necessary
        logger.info(f"CREATE {path}/")
        try:
            dest.remove(path)
        except FileNotFoundError:
            pass
        dest.mkdir(path)

    def update_file(path, src_attrs) -> None:
        logger.info(f"UPDATE {path}")
        with src.open(path, "rb") as fl:
            dest.putfo(fl, path)
            dest.utime(path, (src_attrs.st_atime, src_attrs.st_mtime))

    def needs_sync(path, src_attrs) -> bool:
        # general:
        # return True if path not exist on dest
        # for directories:
        # return True if path also is a directory on dest
        # for files:
        # return True if file has same size and mtime on dest
        dest_attrs = dest_files.get(path, None)
        if dest_attrs is None:
            return True

        if is_dir(src_attrs) and is_dir(dest_attrs):
            return False
        elif is_dir(dest_attrs):
            return True
        elif (
            dest_attrs.st_size == src_attrs.st_size
            and dest_attrs.st_mtime == src_attrs.st_mtime
        ):
            return False
        else:
            return True

    dest_files = get_files(dest, ".")

    for path, attrs in get_files(src, ".").items():
        if needs_sync(path, attrs):
            if is_dir(attrs):
                mk_dir(path)
            else:
                update_file(path, attrs)
        else:
            logger.info(f"ok    : {path}")


def my_test():
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
    my_test()

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
