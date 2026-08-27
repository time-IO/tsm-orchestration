from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination import paginate
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_external_sftp,
    create_database_if_not_exists,
    get_repo_parser_detailed,
)
from models import User
from models.ingest_external_sftp import (
    IngestExternalSftpCreate,
    IngestExternalSftpUpdate,
    IngestExternalSftpRead,
)
from models.filters import IngestFilter
from repositories.ingest_external_sftp import IngestExternalSftpRepository
from repositories.parser_detailed import ParserDetailedRepository
from utils import generate_keypair, generate_password

from mqtt import publish_frontend_thing_update

import uuid
import re

router = APIRouter(
    prefix="/ingest/external-sftp",
    tags=["ingest/external-sftp"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external sftp"


@router.get(
    "/",
    response_model=Page[IngestExternalSftpRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalSftpRepository = Depends(get_repo_ingest_external_sftp),
    filters: IngestFilter = Depends(),
    sort_by: str | None = None,
):
    return paginate(
        repo.find_all(
            sort_by=sort_by,
            filters=filters,
            access_scope=AccessScope.from_user(current_user),
        )
    )


@router.get(
    "/{id}", response_model=IngestExternalSftpRead, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalSftpRepository = Depends(get_repo_ingest_external_sftp),
):
    return repo.to_flat(
        repo.find_one(id, access_scope=AccessScope.from_user(current_user))
    )


@router.post(
    "/",
    response_model=IngestExternalSftpRead,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestExternalSftpCreate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalSftpRepository = Depends(get_repo_ingest_external_sftp),
    parser_repo: ParserDetailedRepository = Depends(get_repo_parser_detailed),
):
    if payload.parser_id:
        parser = parser_repo.find_one(
            payload.parser_id, access_scope=AccessScope.from_user(current_user)
        )
        if not parser or parser.permission_group_id != payload.permission_group_id:
            raise HTTPException(status_code=401, detail="Not allowed to use parser")

    private_key, public_key = generate_keypair()

    _uuid = uuid.uuid4()
    bucket_username = re.sub("[^a-z0-9-]+", "", f"ingest-external-sftp-{_uuid}")
    bucket_name = bucket_username
    bucket_password = generate_password(40)

    extra_data = {
        "created_by_id": current_user.id,
        "uuid": _uuid,
        "ssh_private_key": private_key,
        "ssh_public_key": public_key,
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
    response_model=IngestExternalSftpRead,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestExternalSftpUpdate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalSftpRepository = Depends(get_repo_ingest_external_sftp),
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
    repo: IngestExternalSftpRepository = Depends(get_repo_ingest_external_sftp),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
