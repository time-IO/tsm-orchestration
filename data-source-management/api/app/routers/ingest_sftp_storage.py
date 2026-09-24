from dependencies import get_repo_ingest_sftp
from services import s3_storage
from routers._s3_storage_router import build_s3_storage_router

router = build_s3_storage_router(
    prefix="/ingest/sftp",
    tag="ingest/sftp/storage",
    get_repo=get_repo_ingest_sftp,
    extract_access=s3_storage.access_from_sftp,
)
