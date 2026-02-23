from fastapi import APIRouter, Depends
from dependencies import get_current_user, get_repo_ingest_external_api_uba
from models.ingest_external_api_uba import (
    IngestExternalApiUbaCreate,
    IngestExternalApiUbaUpdate,
    IngestExternalApiUbaPublic,
)

router = APIRouter(
    prefix="/ingest/external-api/uba",
    tags=["ingest/external-api/uba"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external api uba"


@router.get(
    "/",
    response_model=list[IngestExternalApiUbaPublic],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_uba),
):
    return repo.find_allowed_all(current_user.permission_group_ids)


@router.get(
    "/{id}", response_model=IngestExternalApiUbaPublic, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_uba),
):
    return repo.find_allowed_one(id, current_user.permission_group_ids)


@router.post(
    "/", response_model=IngestExternalApiUbaPublic, summary=f"Create one {entity_name}"
)
def create(
    *,
    payload: IngestExternalApiUbaCreate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_uba),
):
    extra_data = {"created_by_id": current_user.id}
    return repo.create_allowed(payload, extra_data, current_user.permission_group_ids)


@router.patch(
    "/{id}",
    response_model=IngestExternalApiUbaPublic,
    summary=f"Update one {entity_name}",
)
def update(
    *,
    id: int,
    payload: IngestExternalApiUbaUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_uba),
):
    return repo.update_allowed(id, payload, current_user.permission_group_ids)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_uba),
):
    return repo.delete_allowed(id, current_user.permission_group_ids)
