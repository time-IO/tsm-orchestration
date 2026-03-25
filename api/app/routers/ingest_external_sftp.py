from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination import paginate
from dependencies import (
    get_current_user,
    get_repo_ingest_external_sftp,
    create_database_if_not_exists,
)
from models.ingest_external_sftp import (
    IngestExternalSftpCreate,
    IngestExternalSftpUpdate,
    IngestExternalSftpPublic,
)
from utils import generate_keypair, generate_password

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
    response_model=Page[IngestExternalSftpPublic],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_sftp),
):
    return paginate(repo.find_allowed_all(current_user.permission_group_ids))


@router.get(
    "/{id}", response_model=IngestExternalSftpPublic, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_sftp),
):
    return repo.find_allowed_one(id, current_user.permission_group_ids)


@router.post(
    "/",
    response_model=IngestExternalSftpPublic,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestExternalSftpCreate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_sftp),
):
    private_key, public_key = generate_keypair()

    _uuid = uuid.uuid4()
    bucket_username = re.sub("[^a-z0-9-]+", "", f"ingest-external-sftp-{_uuid}")
    bucket_name = bucket_username
    bucket_password = generate_password(40)

    extra_data = {
        "created_by_id": current_user.id,
        "ssh_private_key": private_key,
        "ssh_public_key": public_key,
        "bucket_name": bucket_name,
        "bucket_username": bucket_username,
        "bucket_password": bucket_password,
    }

    return repo.create_allowed(payload, extra_data, current_user.permission_group_ids)


@router.patch(
    "/{id}",
    response_model=IngestExternalSftpPublic,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestExternalSftpUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_sftp),
):
    return repo.update_allowed(id, payload, current_user.permission_group_ids)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_sftp),
):
    return repo.delete_allowed(id, current_user.permission_group_ids)
