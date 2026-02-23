from fastapi import APIRouter, Depends
from dependencies import (
    get_current_user,
    get_repo_ingest_external_api_the_things_network,
)
from models.ingest_external_api_the_things_network import (
    IngestExternalApiTheThingsNetworkCreate,
    IngestExternalApiTheThingsNetworkUpdate,
    IngestExternalApiTheThingsNetworkPublic,
)

router = APIRouter(
    prefix="/ingest/external-api/the-things-network",
    tags=["ingest/external-api/the-things-network"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external api the things network"


@router.get(
    "/",
    response_model=list[IngestExternalApiTheThingsNetworkPublic],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_the_things_network),
):
    return repo.find_allowed_all(current_user.permission_group_ids)


@router.get(
    "/{id}",
    response_model=IngestExternalApiTheThingsNetworkPublic,
    summary=f"Get one {entity_name}",
)
def read_one(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_the_things_network),
):
    return repo.find_allowed_one(id, current_user.permission_group_ids)


@router.post(
    "/",
    response_model=IngestExternalApiTheThingsNetworkPublic,
    summary=f"Create one {entity_name}",
)
def create(
    *,
    payload: IngestExternalApiTheThingsNetworkCreate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_the_things_network),
):
    extra_data = {"created_by_id": current_user.id}
    return repo.create_allowed(payload, extra_data, current_user.permission_group_ids)


@router.patch(
    "/{id}",
    response_model=IngestExternalApiTheThingsNetworkPublic,
    summary=f"Update one {entity_name}",
)
def update(
    *,
    id: int,
    payload: IngestExternalApiTheThingsNetworkUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_the_things_network),
):
    return repo.update_allowed(id, payload, current_user.permission_group_ids)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_external_api_the_things_network),
):
    return repo.delete_allowed(id, current_user.permission_group_ids)
