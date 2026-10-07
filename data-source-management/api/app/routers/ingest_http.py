from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination import paginate
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_http,
    create_database_if_not_exists,
    get_repo_parser_detailed,
)
from models import User
from models.ingest_http import (
    IngestHttpCreate,
    IngestHttpUpdate,
    IngestHttpRead,
)
from models.filters import IngestFilter
from repositories.ingest_http import IngestHttpRepository
from repositories.parser_detailed import ParserDetailedRepository
from utils import generate_password
import uuid
import re

from mqtt import publish_frontend_thing_update

router = APIRouter(
    prefix="/ingest/http",
    tags=["ingest/http"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest http"


@router.get(
    "/",
    response_model=Page[IngestHttpRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestHttpRepository = Depends(get_repo_ingest_http),
    filters: IngestFilter = Depends(),
    sort_by: str | None = None,
):
    return paginate(
        repo.find_all(
            access_scope=AccessScope.from_user(current_user),
            sort_by=sort_by,
            filters=filters,
        )
    )


@router.get("/{id}", response_model=IngestHttpRead, summary=f"Get one {entity_name}")
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestHttpRepository = Depends(get_repo_ingest_http),
):
    return repo.to_flat(
        repo.find_one(id, access_scope=AccessScope.from_user(current_user))
    )


@router.post(
    "/",
    response_model=IngestHttpRead,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestHttpCreate,
    current_user: User = Depends(get_current_user),
    repo: IngestHttpRepository = Depends(get_repo_ingest_http),
    parser_repo: ParserDetailedRepository = Depends(get_repo_parser_detailed),
):
    if payload.parser_id:
        parser = parser_repo.find_one(
            payload.parser_id, access_scope=AccessScope.from_user(current_user)
        )
        if not parser or parser.permission_group_id != payload.permission_group_id:
            raise HTTPException(status_code=401, detail="Not allowed to use parser")

    # HTTP doesn't need SSH keypairs like SFTP does, but it does get its own
    # internal S3 bucket to deliver posted files into.
    _uuid = uuid.uuid4()
    bucket_username = re.sub("[^a-z0-9-]+", "", f"ingest-http-{_uuid}")
    bucket_name = bucket_username
    bucket_password = generate_password(40)

    extra_data = {
        "created_by_id": current_user.id,
        "uuid": _uuid,
        "bucket_name": bucket_name,
        "bucket_username": bucket_username,
        "bucket_password": bucket_password,
    }

    entity = repo.create(
        payload,
        extra_data,
        access_scope=AccessScope.from_user(current_user),
    )
    publish_frontend_thing_update(entity)
    return repo.to_flat(entity)


@router.patch(
    "/{id}",
    response_model=IngestHttpRead,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestHttpUpdate,
    current_user: User = Depends(get_current_user),
    repo: IngestHttpRepository = Depends(get_repo_ingest_http),
    parser_repo: ParserDetailedRepository = Depends(get_repo_parser_detailed),
):
    if payload.parser_id:
        parser = parser_repo.find_one(
            payload.parser_id, access_scope=AccessScope.from_user(current_user)
        )
        if not parser or parser.permission_group_id != payload.permission_group_id:
            raise HTTPException(status_code=401, detail="Not allowed to use parser")

    entity = repo.update(id, payload, access_scope=AccessScope.from_user(current_user))
    publish_frontend_thing_update(entity)
    return repo.to_flat(entity)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestHttpRepository = Depends(get_repo_ingest_http),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
