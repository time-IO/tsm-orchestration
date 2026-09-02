"""S3 object-storage access for SFTP-style ingests.

Both ``ingest_sftp`` and ``ingest_external_sftp`` own a bucket with a set of S3
credentials (an access key / secret key pair, the secret decrypted transparently
on read). The two entity types name these fields differently, so callers convert
an entity into a :class:`BucketAccess` via the ``access_from_*`` helpers before
calling into this module.

This is a thin, per-request wrapper over ``boto3`` used by the S3 explorer
endpoints to list, upload, download and create directories against any
S3-compatible endpoint. All traffic is proxied through the API so the browser
never sees the credentials or the storage endpoint.
"""

import logging
from typing import BinaryIO, NamedTuple

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException

from config import settings

logger = logging.getLogger("app.services.s3_storage")

# S3 keys are grouped into "folders" by this delimiter.
DELIMITER = "/"

# Errors that mean "the object/bucket does not exist" rather than a real failure.
_NOT_FOUND_CODES = {"NoSuchKey", "NoSuchBucket", "NotFound", "404"}


class BucketAccess(NamedTuple):
    """S3 credentials scoped to a single bucket."""

    bucket: str
    access_key: str
    secret_key: str


def access_from_sftp(entity) -> BucketAccess:
    """Build bucket access for an ``ingest_sftp`` entity."""
    return BucketAccess(entity.bucket_name, entity.username, entity.password)


def access_from_external_sftp(entity) -> BucketAccess:
    """Build bucket access for an ``ingest_external_sftp`` entity."""
    return BucketAccess(
        entity.bucket_name, entity.bucket_username, entity.bucket_password
    )


def _endpoint_url() -> str:
    """Build the S3 endpoint URL from settings.

    ``S3_ENDPOINT`` is a host[:port] (e.g. ``object-storage:9000`` or
    ``s3.example.org``); ``S3_SECURE`` selects http vs https. A full URL with an
    explicit scheme is accepted as-is, so external providers can also be used.
    """
    raw = settings.S3_ENDPOINT.strip()
    if not raw:
        logger.error("S3_ENDPOINT is not configured")
        raise HTTPException(status_code=503, detail="Object storage is not configured.")
    if "://" in raw:
        return raw
    scheme = "https" if settings.S3_SECURE else "http"
    return f"{scheme}://{raw}"


def build_client(access: BucketAccess):
    """Build an S3 client scoped to the given bucket credentials."""
    return boto3.client(
        "s3",
        endpoint_url=_endpoint_url(),
        aws_access_key_id=access.access_key,
        aws_secret_access_key=access.secret_key,
        region_name=settings.S3_REGION,
        # path-style addressing works for MinIO / container endpoints as well as
        # AWS, unlike virtual-hosted style which needs DNS per bucket.
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def _handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ClientError):
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in _NOT_FOUND_CODES:
            return HTTPException(status_code=404, detail="Object not found.")
        logger.error("S3 error (%s): %s", code, exc)
    else:
        logger.error("S3 connection error: %s", exc)
    return HTTPException(status_code=502, detail="Object storage request failed.")


def list_objects(access: BucketAccess, prefix: str = "") -> list[dict]:
    """List objects (non-recursive, folder-style) under ``prefix``."""
    client = build_client(access)
    try:
        result: list[dict] = []
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=access.bucket, Prefix=prefix, Delimiter=DELIMITER
        ):
            # sub-folders come back as CommonPrefixes
            for common in page.get("CommonPrefixes", []):
                key = common["Prefix"]
                result.append(
                    {
                        "name": key[len(prefix) :] if prefix else key,
                        "key": key,
                        "size": 0,
                        "last_modified": None,
                        "is_dir": True,
                    }
                )
            for obj in page.get("Contents", []):
                key = obj["Key"]
                # skip the zero-byte placeholder for the current folder itself
                if key == prefix:
                    continue
                modified = obj.get("LastModified")
                result.append(
                    {
                        "name": key[len(prefix) :] if prefix else key,
                        "key": key,
                        "size": obj.get("Size", 0),
                        "last_modified": modified.isoformat() if modified else None,
                        "is_dir": False,
                    }
                )
        return result
    except (ClientError, BotoCoreError) as exc:
        raise _handle_error(exc)


def stat(access: BucketAccess, key: str) -> dict:
    """Return size and content type for a single object."""
    client = build_client(access)
    try:
        resp = client.head_object(Bucket=access.bucket, Key=key)
        return {
            "size": resp.get("ContentLength", 0),
            "content_type": resp.get("ContentType") or "application/octet-stream",
        }
    except (ClientError, BotoCoreError) as exc:
        raise _handle_error(exc)


def get_object_stream(access: BucketAccess, key: str):
    """Return the streaming body for an object.

    The caller is responsible for closing the body (the download endpoint does so
    inside its streaming generator).
    """
    client = build_client(access)
    try:
        return client.get_object(Bucket=access.bucket, Key=key)["Body"]
    except (ClientError, BotoCoreError) as exc:
        raise _handle_error(exc)


def put_object(
    access: BucketAccess,
    key: str,
    data: BinaryIO,
    content_type: str = "application/octet-stream",
) -> None:
    """Stream an uploaded file into the bucket under ``key``.

    ``upload_fileobj`` streams and switches to multipart automatically, so files
    of unknown/large size never need to be buffered in memory.
    """
    client = build_client(access)
    try:
        client.upload_fileobj(
            data,
            access.bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
    except (ClientError, BotoCoreError) as exc:
        raise _handle_error(exc)


def create_directory(access: BucketAccess, key: str) -> None:
    """Create a folder placeholder (a zero-byte object whose key ends in '/')."""
    if not key.endswith(DELIMITER):
        key = f"{key}{DELIMITER}"
    client = build_client(access)
    try:
        client.put_object(Bucket=access.bucket, Key=key, Body=b"")
    except (ClientError, BotoCoreError) as exc:
        raise _handle_error(exc)
