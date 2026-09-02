from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination import paginate
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_external_api_neutron_monitor,
    create_database_if_not_exists,
)
from models import User
from models.ingest_external_api_neutron_monitor import (
    IngestExternalApiNeutronMonitorCreate,
    IngestExternalApiNeutronMonitorUpdate,
    IngestExternalApiNeutronMonitorRead,
)
from models.filters import IngestExternalApiFilter
from mqtt import publish_frontend_thing_update
from repositories.ingest_external_api_neutron_monitor import (
    IngestExternalApiNeutronMonitorRepository,
)

router = APIRouter(
    prefix="/ingest/external-api/neutron-monitor",
    tags=["ingest/external-api/neutron-monitor"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external api neutron monitor"


@router.get(
    "/",
    response_model=Page[IngestExternalApiNeutronMonitorRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiNeutronMonitorRepository = Depends(
        get_repo_ingest_external_api_neutron_monitor
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
    response_model=IngestExternalApiNeutronMonitorRead,
    summary=f"Get one {entity_name}",
)
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiNeutronMonitorRepository = Depends(
        get_repo_ingest_external_api_neutron_monitor
    ),
):
    return repo.to_flat(
        repo.find_one(id, access_scope=AccessScope.from_user(current_user))
    )


@router.post(
    "/",
    response_model=IngestExternalApiNeutronMonitorRead,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestExternalApiNeutronMonitorCreate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiNeutronMonitorRepository = Depends(
        get_repo_ingest_external_api_neutron_monitor
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
    response_model=IngestExternalApiNeutronMonitorRead,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestExternalApiNeutronMonitorUpdate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalApiNeutronMonitorRepository = Depends(
        get_repo_ingest_external_api_neutron_monitor
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
    repo: IngestExternalApiNeutronMonitorRepository = Depends(
        get_repo_ingest_external_api_neutron_monitor
    ),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
