from fastapi import APIRouter, Depends
from ..dependencies import get_current_user, get_repo_ingest_mqtt
from ..models.ingest_mqtt import (
    IngestMqttCreate,
    IngestMqttPublic,
    IngestMqttUpdate,
)

router = APIRouter(
    prefix="/ingest/mqtt",
    tags=["ingest/mqtt"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest mqtt"


@router.get(
    "/", response_model=list[IngestMqttPublic], summary=f"Get a list of {entity_name}"
)
def read_list(
    *,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_mqtt),
):
    return repo.find_allowed_all(current_user.permission_group_ids)


@router.get("/{id}", response_model=IngestMqttPublic, summary=f"Get one {entity_name}")
def read_one(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_mqtt),
):
    return repo.find_allowed_one(id, current_user.permission_group_ids)


@router.post("/", response_model=IngestMqttPublic, summary=f"Create one {entity_name}")
def create(
    *,
    payload: IngestMqttCreate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_mqtt),
):
    extra_data = {"created_by_id": current_user.id}
    # todo username
    # todo password (encrypted)
    # todo password_hashed (encrypted)
    # todo uri
    return repo.create_allowed(payload, extra_data, current_user.permission_group_ids)


@router.patch(
    "/{id}", response_model=IngestMqttPublic, summary=f"Update one {entity_name}"
)
def update(
    *,
    id: int,
    payload: IngestMqttUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_mqtt),
):
    return repo.update_allowed(id, payload, current_user.permission_group_ids)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_mqtt),
):
    return repo.delete_allowed(id, current_user.permission_group_ids)
