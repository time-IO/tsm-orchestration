from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination import paginate
from dependencies import (
    get_current_user,
    get_repo_ingest_external_api_sensoto,
    create_database_if_not_exists,
)
from models import User
from models.ingest_external_api_sensoto import (
    IngestExternalApiSensotoCreate,
    IngestExternalApiSensotoUpdate,
    IngestExternalApiSensotoRead,
)
from models.filters import IngestExternalApiFilter
from mqtt import publish_frontend_thing_update
from repositories.ingest_external_api_sensoto import (
    IngestExternalApiSensotoRepository,
)

router = APIRouter(
    prefix="/ingest/external-api/sensoto",
    tags=["ingest/external-api/sensoto"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external api sensoto"


@router.get(
    "/",
    response_model=Page[IngestExternalApiSensotoRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiSensotoRepository = Depends(
        get_repo_ingest_external_api_sensoto
    ),
    filters: IngestExternalApiFilter = Depends(),
    sort_by: str | None = None,
):
    return paginate(
        repo.find_all(current_user.permission_group_ids, sort_by, filters=filters)
    )


@router.get(
    "/{id}",
    response_model=IngestExternalApiSensotoRead,
    summary=f"Get one {entity_name}",
)
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiSensotoRepository = Depends(
        get_repo_ingest_external_api_sensoto
    ),
):
    return repo.to_flat(
        repo.find_one(
            id, permission_group_ids_of_user=current_user.permission_group_ids
        )
    )


@router.post(
    "/",
    response_model=IngestExternalApiSensotoRead,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestExternalApiSensotoCreate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiSensotoRepository = Depends(
        get_repo_ingest_external_api_sensoto
    ),
):
    extra_data = {"created_by_id": current_user.id}
    entity = repo.create(
        payload,
        extra_data,
        permission_group_ids_of_user=current_user.permission_group_ids,
    )
    publish_frontend_thing_update(entity)
    return repo.to_flat(entity)


@router.patch(
    "/{id}",
    response_model=IngestExternalApiSensotoRead,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestExternalApiSensotoUpdate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiSensotoRepository = Depends(
        get_repo_ingest_external_api_sensoto
    ),
):
    entity = repo.update(
        id, payload, permission_group_ids_of_user=current_user.permission_group_ids
    )
    publish_frontend_thing_update(entity)
    return repo.to_flat(entity)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiSensotoRepository = Depends(
        get_repo_ingest_external_api_sensoto
    ),
):
    return repo.delete(
        id, permission_group_ids_of_user=current_user.permission_group_ids
    )
