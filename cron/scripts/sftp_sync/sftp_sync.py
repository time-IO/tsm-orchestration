#!/usr/bin/env python
from __future__ import annotations

import abc
import os
import stat
import sys
import time
from dataclasses import dataclass
from typing import IO
from contextlib import contextmanager

import minio
import psycopg
from minio.datatypes import Object as MinioObject, Bucket
from paramiko import (
    SSHClient,
    WarningPolicy,
    SFTPClient,
    SFTPAttributes,
    RejectPolicy,
    MissingHostKeyPolicy,
)
from paramiko.config import SSH_PORT
import logging

logger = logging.getLogger(__name__)


class RemoteFS(abc.ABC):

    files: dict[str]

    @abc.abstractmethod
    def exist(self, path: str) -> bool: ...
    @abc.abstractmethod
    def is_dir(self, path: str) -> bool: ...
    @abc.abstractmethod
    def last_modified(self, path: str) -> float: ...
    @abc.abstractmethod
    def size(self, path: str) -> int: ...

    @abc.abstractmethod
    def open(self, path: str) -> IO[bytes]: ...
    @abc.abstractmethod
    def put(self, path: str, fo: IO[bytes], size: int) -> None: ...
    @abc.abstractmethod
    def mkdir(self, path: str) -> None: ...

    def update(self, other: RemoteFS, path) -> None:
        """
        Update or create a file at the same location as in the other
        file system.
        """
        if other.is_dir(path):
            raise ValueError(f"Cannot update a directory")
        if self.exist(path):
            logger.debug(f"UPDATE {path}")
        else:
            logger.debug(f"CREATE {path}")
        with other.open(path) as fo:
            self.put(path, fo, other.size(path))


class MinioFS(RemoteFS):

    cl: minio.Minio
    files: dict[str, MinioObject]

    @classmethod
    def from_credentials(
        cls,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str | None = None,
        secure: bool = True,
    ):
        cl = minio.Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        return cls(client=cl, bucket_name=bucket_name)

    def __init__(
        self,
        client: minio.Minio,
        bucket_name: str,
    ) -> None:
        self.cl = client
        self.bucket_name = bucket_name
        self._get_files()

    def _get_files(self):
        self.files = {
            file.object_name: file
            for file in self.cl.list_objects(self.bucket_name, recursive=True)
        }

    def exist(self, path: str):
        return path in self.files

    def size(self, path: str):
        if not self.exist(path):
            raise FileNotFoundError(path)
        return self.files[path].size

    def is_dir(self, path: str):
        if not self.exist(path):
            raise FileNotFoundError(path)
        return self.files[path].is_dir

    def last_modified(self, path: str) -> float:
        if not self.exist(path):
            raise FileNotFoundError(path)
        return time.mktime(self.files[path].last_modified.timetuple())

    def put(self, path: str, fo: IO[bytes], size: int):
        self.cl.put_object(
            bucket_name=self.bucket_name, object_name=path, data=fo, length=size
        )

    @contextmanager
    def open(self, path) -> IO[bytes]:
        if not self.exist(path):
            raise FileNotFoundError(path)
        resp = None
        try:
            resp = self.cl.get_object(bucket_name=self.bucket_name, object_name=path)
            yield resp
        finally:
            if resp is not None:
                resp.close()
                resp.release_conn()

    def mkdir(self, path: str):
        # In Minio directories are created
        # automatically when files are created.
        pass


class FtpFS(RemoteFS):

    cl: SFTPClient
    files: dict[str, SFTPAttributes]

    @classmethod
    def from_credentials(
        cls,
        uri,
        username,
        password,
        path,
        keyfile_path=None,
        missing_host_key_policy=None,
    ):
        host = uri.split(":")[0]
        port = int(f"{uri}:".split(":")[1] or SSH_PORT)
        ssh = SSHClient()
        if missing_host_key_policy is not None:
            ssh.set_missing_host_key_policy(missing_host_key_policy)
        ssh.connect(
            hostname=host,
            port=int(port),
            username=username,
            password=password or None,
            key_filename=keyfile_path,
            look_for_keys=False,  # todo maybe ?
            allow_agent=False,
            compress=True,
        )
        cl = ssh.open_sftp()
        return cls(cl, path)

    def __init__(self, client: SFTPClient, path: str = ".") -> None:
        self.cl = client
        self.path = path
        self.files = {}
        self.cl.chdir(self.path)
        self._get_files()

    def _get_files(self, path=""):
        # Note that directories always appear
        # before any files from that directory
        # appear.
        dirs = []
        # we must avoid calling listdir_iter multiple
        # times, otherwise it might cause a deadlock.
        # That's why we do not recurse within the loop.
        for attrs in self.cl.listdir_iter(path):
            file_path = os.path.join(path, attrs.filename)
            if stat.S_ISDIR(attrs.st_mode):
                dirs.append(file_path)
            self.files[file_path] = attrs
        for dir_ in dirs:
            self._get_files(dir_)

    def exist(self, path: str):
        return path in self.files

    def size(self, path: str):
        if not self.exist(path):
            raise FileNotFoundError(path)
        return self.files[path].st_size

    def is_dir(self, path: str):
        if not self.exist(path):
            raise FileNotFoundError(path)
        return stat.S_ISDIR(self.files[path].st_mode)

    def last_modified(self, path: str) -> float:
        if not self.exist(path):
            raise FileNotFoundError(path)
        return self.files[path].st_mtime

    def put(self, path: str, fo: IO[bytes], size: int):
        self.cl.putfo(fl=fo, remotepath=path, file_size=size)

    def mkdir(self, path: str) -> None:
        logger.debug(f"CREATE {path}")
        self.cl.mkdir(path)

    @contextmanager
    def open(self, path):
        if not self.exist(path):
            raise FileNotFoundError(path)
        with self.cl.open(path, mode="r") as fo:
            yield fo


@dataclass
class FtpMeta:
    uri: str
    username: str
    sync_dir: str | None = None
    password: str | None = None
    ssh_priv_key: str = None


def get_internal_ftp(conn, thing_id) -> tuple[str, str, str, str]:
    """Returns (uri, access_key, secret_key, bucket_name)"""
    with conn.cursor() as cur:
        return cur.execute(
            "SELECT r.fileserver_uri, r.access_key, r.secret_key, r.bucket "
            "FROM tsm_thing t JOIN tsm_rawdatastorage r ON t.id = r.thing_id "
            "WHERE t.thing_id = %s",
            [thing_id],
        ).fetchone()


def get_external_ftp(conn, thing_id) -> tuple[str, str, str, str]:
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
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) != 2:
        raise ValueError("Expected a thing_id as first and only argument.")
    thing_id = sys.argv[1]

    for k in ["SSH_PRIV_KEY_PATH", "FTP_AUTH_DB_URI"]:
        if (os.environ.get(k) or None) is None:
            raise EnvironmentError("Environment variable {k} must be set")
    ssh_priv_key = os.path.join(os.environ["SSH_KEYFILE_DIR"], f"{thing_id}")
    dsn = os.environ["FTP_AUTH_DB_DSN"]

    with psycopg.connect(dsn) as conn:
        ftp_ext = get_external_ftp(conn, thing_id)
        ftp_int = get_internal_ftp(conn, thing_id)

    target = MinioFS.from_credentials(*ftp_int, secure=True)
    source = FtpFS.from_credentials(
        *ftp_ext, keyfile_path=ssh_priv_key, missing_host_key_policy=WarningPolicy
    )
    sync(source, target)
