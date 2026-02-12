from fastapi import APIRouter, Depends
from ..dependencies import get_current_user, get_repo_ingest_external_api_tsystems
from ..models.ingest_external_api_tsystems import (
    IngestExternalApiTSystemsCreate,
    IngestExternalApiTSystemsUpdate,
    IngestExternalApiTSystemsPublic,
)

router = APIRouter(
    prefix="/ingest/external-api/tsystems",
    tags=["ingest/external-api/tsystems"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external api tsystems"


@router.get(
    "/",
    response_model=list[IngestExternalApiTSystemsPublic],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_tsystems),
):
    return repo.find_allowed_all(current_user.permission_group_ids)


@router.get(
    "/{id}",
    response_model=IngestExternalApiTSystemsPublic,
    summary=f"Get one {entity_name}",
)
def read_one(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_tsystems),
):
    return repo.find_allowed_one(id, current_user.permission_group_ids)


@router.post(
    "/",
    response_model=IngestExternalApiTSystemsPublic,
    summary=f"Create one {entity_name}",
)
def create(
    *,
    payload: IngestExternalApiTSystemsCreate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_tsystems),
):
    extra_data = {"created_by_id": current_user.id}
    return repo.create_allowed(payload, extra_data, current_user.permission_group_ids)


@router.patch(
    "/{id}",
    response_model=IngestExternalApiTSystemsPublic,
    summary=f"Update one {entity_name}",
)
def update(
    *,
    id: int,
    payload: IngestExternalApiTSystemsUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_tsystems),
):
    return repo.update_allowed(id, payload, current_user.permission_group_ids)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_tsystems),
):
    return repo.delete_allowed(id, current_user.permission_group_ids)
