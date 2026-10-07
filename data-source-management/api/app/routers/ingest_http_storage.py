from dependencies import get_repo_ingest_http
from services import s3_storage
from routers._s3_storage_router import build_s3_storage_router

router = build_s3_storage_router(
    prefix="/ingest/http",
    tag="ingest/http/storage",
    get_repo=get_repo_ingest_http,
    extract_access=s3_storage.access_from_http,
)
