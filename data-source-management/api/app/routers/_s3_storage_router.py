"""Shared S3 explorer router used by the SFTP-style ingest types.

``ingest_sftp`` and ``ingest_external_sftp`` both expose the same file-explorer
endpoints over their MinIO bucket; only the URL prefix, the repository used to
resolve/authorise the entity, and how bucket credentials are read from that
entity differ. :func:`build_s3_storage_router` captures those three differences
so the endpoint bodies live in one place.
"""

import os
from typing import Callable
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from access_scope import AccessScope
from dependencies import get_current_user
from models import User
from services import s3_storage
from services.s3_storage import BucketAccess

# stream downloads in 64 KiB chunks
DOWNLOAD_CHUNK_SIZE = 64 * 1024


def build_s3_storage_router(
    *,
    prefix: str,
    tag: str,
    get_repo: Callable,
    extract_access: Callable[[object], BucketAccess],
) -> APIRouter:
    router = APIRouter(
        prefix=prefix,
        tags=[tag],
        responses={404: {"description": "Not found"}},
        dependencies=[Depends(get_current_user)],
    )

    def _access(id: int, current_user: User, repo) -> BucketAccess:
        entity = repo.find_one(id, access_scope=AccessScope.from_user(current_user))
        return extract_access(entity)

    @router.get("/{id}/files", summary="List files in the ingest bucket")
    def list_files(
        *,
        id: int,
        prefix: str = "",
        current_user: User = Depends(get_current_user),
        repo=Depends(get_repo),
    ):
        return s3_storage.list_objects(_access(id, current_user, repo), prefix=prefix)

    @router.get("/{id}/files/download", summary="Download a file from the bucket")
    def download_file(
        *,
        id: int,
        key: str,
        current_user: User = Depends(get_current_user),
        repo=Depends(get_repo),
    ):
        access = _access(id, current_user, repo)
        meta = s3_storage.stat(access, key)
        body = s3_storage.get_object_stream(access, key)

        def iterator():
            try:
                yield from body.iter_chunks(DOWNLOAD_CHUNK_SIZE)
            finally:
                body.close()

        filename = os.path.basename(key.rstrip("/")) or "download"
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            "Content-Length": str(meta["size"]),
        }
        return StreamingResponse(
            iterator(), media_type=meta["content_type"], headers=headers
        )

    @router.post("/{id}/files/upload", summary="Upload a file to the bucket")
    def upload_file(
        *,
        id: int,
        file: UploadFile = File(...),
        prefix: str = Form(""),
        current_user: User = Depends(get_current_user),
        repo=Depends(get_repo),
    ):
        access = _access(id, current_user, repo)
        key = f"{prefix}{file.filename}"
        s3_storage.put_object(
            access,
            key,
            file.file,
            content_type=file.content_type or "application/octet-stream",
        )
        return {"ok": True, "key": key}

    @router.post("/{id}/files/directory", summary="Create a directory in the bucket")
    def create_directory(
        *,
        id: int,
        name: str = Form(...),
        prefix: str = Form(""),
        current_user: User = Depends(get_current_user),
        repo=Depends(get_repo),
    ):
        clean_name = name.strip().strip("/")
        if not clean_name or "/" in clean_name:
            raise HTTPException(status_code=422, detail="Invalid directory name.")
        key = f"{prefix}{clean_name}/"
        s3_storage.create_directory(_access(id, current_user, repo), key)
        return {"ok": True, "key": key}

    return router
