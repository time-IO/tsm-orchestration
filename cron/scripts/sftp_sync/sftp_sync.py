#!/usr/bin/env python
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import psycopg
from paramiko import SSHClient


@dataclass
class FtpMeta:
    uri: str
    path: str
    username: str
    password: str = None

    def remote_dir(self) -> str:
        return f"{self.uri}/{self.path}"

    def need_ssh_key(self):
        return bool(self.password)


def connect_internal_ftp():
    pass


def connect_external_ftp():
    pass


def get_credentials(dsn, thing_id):
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT r.fileserver_uri, r.bucket, r.access_key, r.secret_key "
                # fixme
                # ",t.ext_sftp_uri, t.ext_sftp_path, t.ext_sftp_username, t.ext_sftp_password "
                "FROM tsm_thing t "
                "JOIN tsm_rawdatastorage r ON t.id = r.thing_id "
                "WHERE t.thing_id = %s",
                [thing_id],
            )
            r = cur.fetchone()
            # fixme
            if len(r) == 4:
                r = r + r
    internal = FtpMeta(*r[:4])
    external = FtpMeta(*r[4:])
    return internal, external


def connect(ftp: FtpMeta):
    client = SSHClient()
    client.load_system_host_keys()
    client.connect("ssh.example.com")
    stdin, stdout, stderr = client.exec_command("ls -l")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Expected a thing_id as first and only argument.")
    thing_id = sys.argv[1]

    for k in ["SSH_PRIV_KEY_PATH", "FTP_AUTH_DB_URI"]:
        if (os.environ.get(k) or None) is None:
            raise EnvironmentError("Environment variable {k} must be set")
    ssh_key = os.environ["SSH_PRIV_KEY_PATH"]
    dsn = os.environ["FTP_AUTH_DB_URI"]

    iftp, eftp = get_credentials(dsn, thing_id)
    print(iftp)
