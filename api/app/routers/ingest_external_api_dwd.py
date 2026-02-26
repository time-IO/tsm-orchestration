from fastapi import APIRouter, Depends
from dependencies import (
    get_current_user,
    get_repo_ingest_external_api_dwd,
    create_database_if_not_exists,
)
from models.ingest_external_api_dwd import (
    IngestExternalApiDwdCreate,
    IngestExternalApiDwdUpdate,
    IngestExternalApiDwdPublic,
)

router = APIRouter(
    prefix="/ingest/external-api/dwd",
    tags=["ingest/external-api/dwd"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external api dwd"


@router.get(
    "/",
    response_model=list[IngestExternalApiDwdPublic],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_dwd),
):
    return repo.find_allowed_all(current_user.permission_group_ids)


@router.get(
    "/{id}", response_model=IngestExternalApiDwdPublic, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_dwd),
):
    return repo.find_allowed_one(id, current_user.permission_group_ids)


@router.post(
    "/",
    response_model=IngestExternalApiDwdPublic,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestExternalApiDwdCreate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_dwd),
):
    extra_data = {"created_by_id": current_user.id}
    return repo.create_allowed(payload, extra_data, current_user.permission_group_ids)


@router.patch(
    "/{id}",
    response_model=IngestExternalApiDwdPublic,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestExternalApiDwdUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_dwd),
):
    return repo.update_allowed(id, payload, current_user.permission_group_ids)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_dwd),
):
    return repo.delete_allowed(id, current_user.permission_group_ids)
