from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination import paginate
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_external_api_myatmosphere,
    create_database_if_not_exists,
)
from models import User
from models.ingest_external_api_myatmosphere import (
    IngestExternalApiMyAtmosphereCreate,
    IngestExternalApiMyAtmosphereUpdate,
    IngestExternalApiMyAtmosphereRead,
)
from models.filters import IngestExternalApiFilter
from mqtt import publish_frontend_thing_update
from repositories.ingest_external_api_myatmosphere import (
    IngestExternalApiMyAtmosphereRepository,
)

router = APIRouter(
    prefix="/ingest/external-api/myatmosphere",
    tags=["ingest/external-api/myatmosphere"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external api myatmosphere"


@router.get(
    "/",
    response_model=Page[IngestExternalApiMyAtmosphereRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiMyAtmosphereRepository = Depends(
        get_repo_ingest_external_api_myatmosphere
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
    response_model=IngestExternalApiMyAtmosphereRead,
    summary=f"Get one {entity_name}",
)
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiMyAtmosphereRepository = Depends(
        get_repo_ingest_external_api_myatmosphere
    ),
):
    return repo.to_flat(
        repo.find_one(id, access_scope=AccessScope.from_user(current_user))
    )


@router.post(
    "/",
    response_model=IngestExternalApiMyAtmosphereRead,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestExternalApiMyAtmosphereCreate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiMyAtmosphereRepository = Depends(
        get_repo_ingest_external_api_myatmosphere
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
    response_model=IngestExternalApiMyAtmosphereRead,
    summary=f"Update one {entity_name}",
)
def update(
    *,
    id: int,
    payload: IngestExternalApiMyAtmosphereUpdate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiMyAtmosphereRepository = Depends(
        get_repo_ingest_external_api_myatmosphere
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
    repo: IngestExternalApiMyAtmosphereRepository = Depends(
        get_repo_ingest_external_api_myatmosphere
    ),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
