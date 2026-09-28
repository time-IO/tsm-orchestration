from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination import paginate
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_external_api_zentra,
    create_database_if_not_exists,
)
from models import User
from models.ingest_external_api_zentra import (
    IngestExternalApiZentraCreate,
    IngestExternalApiZentraUpdate,
    IngestExternalApiZentraRead,
)
from models.filters import IngestExternalApiFilter
from mqtt import publish_frontend_thing_update
from repositories.ingest_external_api_zentra import (
    IngestExternalApiZentraRepository,
)

router = APIRouter(
    prefix="/ingest/external-api/zentra",
    tags=["ingest/external-api/zentra"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external api zentra"


@router.get(
    "/",
    response_model=Page[IngestExternalApiZentraRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiZentraRepository = Depends(
        get_repo_ingest_external_api_zentra
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
    response_model=IngestExternalApiZentraRead,
    summary=f"Get one {entity_name}",
)
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiZentraRepository = Depends(
        get_repo_ingest_external_api_zentra
    ),
):
    return repo.to_flat(
        repo.find_one(id, access_scope=AccessScope.from_user(current_user))
    )


@router.post(
    "/",
    response_model=IngestExternalApiZentraRead,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestExternalApiZentraCreate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiZentraRepository = Depends(
        get_repo_ingest_external_api_zentra
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
    response_model=IngestExternalApiZentraRead,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestExternalApiZentraUpdate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiZentraRepository = Depends(
        get_repo_ingest_external_api_zentra
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
    repo: IngestExternalApiZentraRepository = Depends(
        get_repo_ingest_external_api_zentra
    ),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))