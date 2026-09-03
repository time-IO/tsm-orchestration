from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination import paginate
from dependencies import (
    get_current_user,
    get_repo_ingest_external_mqtt,
    create_database_if_not_exists,
    get_repo_parser_detailed,
)
from models import User
from models.ingest_external_mqtt import (
    IngestExternalMqttCreate,
    IngestExternalMqttUpdate,
    IngestExternalMqttRead,
)
from models.filters import IngestFilter
from repositories.ingest_external_mqtt import IngestExternalMqttRepository
from repositories.parser_detailed import ParserDetailedRepository

from mqtt import publish_frontend_thing_update

router = APIRouter(
    prefix="/ingest/external-mqtt",
    tags=["ingest/external-mqtt"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external mqtt"


@router.get(
    "/",
    response_model=Page[IngestExternalMqttRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalMqttRepository = Depends(get_repo_ingest_external_mqtt),
    filters: IngestFilter = Depends(),
    sort_by: str | None = None,
):
    return paginate(
        repo.find_all(current_user.permission_group_ids, sort_by, filters=filters)
    )


@router.get(
    "/{id}", response_model=IngestExternalMqttRead, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalMqttRepository = Depends(get_repo_ingest_external_mqtt),
):
    return repo.to_flat(
        repo.find_one(
            id, permission_group_ids_of_user=current_user.permission_group_ids
        )
    )


@router.post(
    "/",
    response_model=IngestExternalMqttRead,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestExternalMqttCreate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalMqttRepository = Depends(get_repo_ingest_external_mqtt),
    parser_repo: ParserDetailedRepository = Depends(get_repo_parser_detailed),
):
    if payload.parser_id:
        parser = parser_repo.find_one(
            payload.parser_id, current_user.permission_group_ids
        )
        if not parser or parser.permission_group_id != payload.permission_group_id:
            raise HTTPException(status_code=401, detail="Not allowed to use parser")

    # MQTT doesn't need SSH keypairs or bucket credentials like SFTP does
    extra_data = {
        "created_by_id": current_user.id,
    }

    entity = repo.create(
        payload,
        extra_data,
        permission_group_ids_of_user=current_user.permission_group_ids,
    )
    publish_frontend_thing_update(entity)
    return repo.to_flat(entity)


@router.patch(
    "/{id}",
    response_model=IngestExternalMqttRead,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestExternalMqttUpdate,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalMqttRepository = Depends(get_repo_ingest_external_mqtt),
    parser_repo: ParserDetailedRepository = Depends(get_repo_parser_detailed),
):
    if payload.parser_id:
        parser = parser_repo.find_one(
            payload.parser_id, current_user.permission_group_ids
        )
        if not parser or parser.permission_group_id != payload.permission_group_id:
            raise HTTPException(status_code=401, detail="Not allowed to use parser")

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
    repo: IngestExternalMqttRepository = Depends(get_repo_ingest_external_mqtt),
):
    return repo.delete(
        id, permission_group_ids_of_user=current_user.permission_group_ids
    )