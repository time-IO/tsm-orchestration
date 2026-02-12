from fastapi import APIRouter, Depends
from ..dependencies import get_current_user, get_repo_ingest_s3stores
from ..models.ingest_s3store import (
    IngestS3StoreCreate,
    IngestS3StorePublic,
    IngestS3StoreUpdate,
)

router = APIRouter(
    prefix="/ingest/s3store",
    tags=["ingest/s3store"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest s3store"


@router.get(
    "/",
    response_model=list[IngestS3StorePublic],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_s3stores),
):
    return repo.find_allowed_all(current_user.permission_group_ids)


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
    "/", response_model=IngestS3StorePublic, summary=f"Create one {entity_name}"
)
def create(
    *,
    payload: IngestS3StoreCreate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_s3stores),
):
    extra_data = {"created_by_id": current_user.id}
    # todo create username, password (+ encrypt), bucket_name
    return repo.create_allowed(payload, extra_data, current_user.permission_group_ids)


@router.patch(
    "/{id}", response_model=IngestS3StorePublic, summary=f"Update one {entity_name}"
)
def update(
    *,
    id: int,
    payload: IngestS3StoreUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_s3stores),
):
    return repo.update_allowed(id, payload, current_user.permission_group_ids)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_s3stores),
):
    return repo.delete_allowed(id, current_user.permission_group_ids)
