from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination import paginate
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_external_api_the_things_network,
    create_database_if_not_exists,
)
from models import User
from models.ingest_external_api_the_things_network import (
    IngestExternalApiTheThingsNetworkCreate,
    IngestExternalApiTheThingsNetworkUpdate,
    IngestExternalApiTheThingsNetworkRead,
)
from models.filters import IngestExternalApiFilter
from mqtt import publish_frontend_thing_update
from repositories.ingest_external_api_the_things_network import (
    IngestExternalApiTheThingsNetworkRepository,
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
    response_model=Page[IngestExternalApiTheThingsNetworkRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiTheThingsNetworkRepository = Depends(
        get_repo_ingest_external_api_the_things_network
    ),
    filters: IngestExternalApiFilter = Depends(),
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
    "/{id}",
    response_model=IngestExternalApiTheThingsNetworkRead,
    summary=f"Get one {entity_name}",
)
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiTheThingsNetworkRepository = Depends(
        get_repo_ingest_external_api_the_things_network
    ),
):
    return repo.to_flat(
        repo.find_one(id, access_scope=AccessScope.from_user(current_user))
    )


@router.post(
    "/",
    response_model=IngestExternalApiTheThingsNetworkRead,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestExternalApiTheThingsNetworkCreate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiTheThingsNetworkRepository = Depends(
        get_repo_ingest_external_api_the_things_network
    ),
):
    extra_data = {"created_by_id": current_user.id}
    entity = repo.create(
        payload,
        extra_data,
        access_scope=AccessScope.from_user(current_user),
    )
    publish_frontend_thing_update(entity)
    return repo.to_flat(entity)


@router.patch(
    "/{id}",
    response_model=IngestExternalApiTheThingsNetworkRead,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestExternalApiTheThingsNetworkUpdate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiTheThingsNetworkRepository = Depends(
        get_repo_ingest_external_api_the_things_network
    ),
):
    entity = repo.update(id, payload, access_scope=AccessScope.from_user(current_user))
    publish_frontend_thing_update(entity)
    return repo.to_flat(entity)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiTheThingsNetworkRepository = Depends(
        get_repo_ingest_external_api_the_things_network
    ),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
