#!/usr/bin/env python3
from __future__ import annotations

import io
import os
import sys
import logging

from paramiko import WarningPolicy
from timeio.crypto import decrypt, get_crypt_key
from timeio.remote_fs import MinioFS, FtpFS, sync
from timeio.feta import Thing

USAGE = """
Usage: sftp_sync.py THING_UUID 
Sync external SFTP files to minio storage.

Arguments
  THING_UUID        UUID of the thing.

Additional set the following environment variables:

  MINIO_URL         Minio URL to sync to.
  MINIO_USER        Minio user with r/w privileges 
  MINIO_PASSWORD    Password for minio user above.
  MINIO_SECURE      Use minio secure connection; [true, false, 1, 0] 
  CONFIGDB_DSN      DB which stores the credentials for the external sftp server 
                    (source of sync) and also the (existing) bucket-name for the 
                    target S3 storage. See also DSN format below. 
                    
  LOG_LEVEL         Set the verbosity, defaults to INFO.
                    [DEBUG, INFO, WARNING, ERROR, CRITICAL]
  FERNET_ENCRYPTION_SECRET  Secret used to decrypt sensitive information from 
                    the Config-DB. 

DSN format: 
  postgresql://[user[:password]@][netloc][:port][/dbname]
"""

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(USAGE)
        exit(1)

    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    for k in [
        "CONFIGDB_DSN",
        "MINIO_URL",
        "MINIO_USER",
        "MINIO_PASSWORD",
        "MINIO_SECURE",
        "FERNET_ENCRYPTION_SECRET",
    ]:
        if not os.environ.get(k):
            raise EnvironmentError(f"Environment variable {k} must be set")
    # ensure True as default
    minio_secure = os.environ["MINIO_SECURE"].lower() not in ["false", "0"]

    thing = Thing.from_uuid(sys.argv[1], dsn=os.environ["CONFIGDB_DSN"])
    logging.getLogger("sftp_sync").info("Thing UUID: %s", thing.uuid)

    target = MinioFS.from_credentials(
        endpoint=os.environ["MINIO_URL"],
        access_key=os.environ["MINIO_USER"],
        secret_key=os.environ["MINIO_PASSWORD"],
        bucket_name=thing.s3_store.bucket,
        secure=minio_secure,
    )

    priv_key = decrypt(thing.ext_sftp.ssh_priv_key, get_crypt_key())
    source = FtpFS.from_credentials(
        uri=thing.ext_sftp.uri,
        username=thing.ext_sftp.user,
        password=thing.ext_sftp.password,
        path=thing.ext_sftp.path,
        keyfile_path=io.StringIO(priv_key),
        missing_host_key_policy=WarningPolicy(),
    )

    sync(source, target, thing.uuid)
