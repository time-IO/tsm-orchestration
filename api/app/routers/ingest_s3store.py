from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination import paginate
from dependencies import (
    get_current_user,
    get_repo_ingest_s3stores,
    create_database_if_not_exists,
    get_repo_csv_parser,
)
from models import BaseRepository, CsvParser
from models.ingest_s3store import (
    IngestS3StoreCreate,
    IngestS3StorePublic,
    IngestS3StoreUpdate,
)
from utils import generate_password
from config import settings
import uuid
import re

router = APIRouter(
    prefix="/ingest/s3store",
    tags=["ingest/s3store"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest s3store"
ingest_type_info = {"ingest_type": "sftp"}


@router.get(
    "/",
    response_model=Page[IngestS3StorePublic],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_s3stores),
    sort_by: str | None = None,
):
    return paginate(repo.find_allowed_all(current_user.permission_group_ids, sort_by))


@router.get(
    "/{id}", response_model=IngestS3StorePublic, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_s3stores),
):
    return repo.find_allowed_one(id, current_user.permission_group_ids)


@router.post(
    "/",
    response_model=IngestS3StorePublic,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestS3StoreCreate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_s3stores),
    parser_repo: BaseRepository[CsvParser] = Depends(get_repo_csv_parser),
):
    parser = parser_repo.find_allowed_one(
        payload.parser_csv_id, current_user.permission_group_ids
    )
    if not parser or parser.permission_group_id != payload.permission_group_id:
        raise HTTPException(status_code=401, detail="Not allowed to use parser")

    _uuid = uuid.uuid4()
    username = re.sub("[^a-z0-9-]+", "", f"ingest-sftp-{_uuid}")
    bucket_name = username
    password = generate_password(40)
    fileserver_uri = settings.SFTP_URI

    extra_data = {
        "created_by_id": current_user.id,
        "uuid": _uuid,
        "username": username,
        "password": password,
        "bucket_name": bucket_name,
        "fileserver_uri": fileserver_uri,
    }
    return repo.create_allowed(
        payload,
        extra_data,
        current_user.permission_group_ids,
        ingest_type_info=ingest_type_info,
    )


@router.patch(
    "/{id}",
    response_model=IngestS3StorePublic,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestS3StoreUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_s3stores),
    parser_repo: BaseRepository[CsvParser] = Depends(get_repo_csv_parser),
):
    parser = None
    if payload.parser_csv_id:
        parser = parser_repo.find_allowed_one(
            payload.parser_csv_id, current_user.permission_group_ids
        )
    return repo.update_ingest_sftp(
        id,
        payload,
        current_user.permission_group_ids,
        ingest_type_info=ingest_type_info,
    )


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_s3stores),
):
    return repo.delete_allowed(id, current_user.permission_group_ids)
