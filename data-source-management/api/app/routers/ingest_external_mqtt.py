from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination import paginate
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_external_mqtt,
    create_database_if_not_exists,
)
from models import User
from models.ingest_external_mqtt import (
    IngestExternalMqttCreate,
    IngestExternalMqttUpdate,
    IngestExternalMqttRead,
)
from models.filters import IngestFilter
from repositories.ingest_external_mqtt import IngestExternalMqttRepository
from utils import generate_password, hash_password
from config import settings
import uuid
import re

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
        repo.find_all(
            access_scope=AccessScope.from_user(current_user),
            sort_by=sort_by,
            filters=filters,
        )
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
        repo.find_one(id, access_scope=AccessScope.from_user(current_user))
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
):
    # MQTT doesn't need SSH keypairs or bucket credentials like SFTP does, but
    # every external_mqtt ingest gets a companion internal MQTT user so Bento
    # can relay the bridged data onto our own broker (see setup_bento.py).
    _uuid = uuid.uuid4()
    internal_mqtt_username = re.sub("[^a-z0-9-]+", "", f"ingest-external-mqtt-{_uuid}")
    internal_mqtt_password = generate_password(40)

    extra_data = {
        "created_by_id": current_user.id,
        "uuid": _uuid,
    }
    internal_mqtt_extra_data = {
        "username": internal_mqtt_username,
        "password": internal_mqtt_password,
        "password_hashed": hash_password(internal_mqtt_password),
        "topic": "mqtt_ingest/" + internal_mqtt_username,
        "uri": settings.INGEST_MQTT_BROKER_URI,
    }

    entity = repo.create(
        payload,
        extra_data,
        internal_mqtt_extra_data,
        access_scope=AccessScope.from_user(current_user),
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
):
    entity = repo.update(id, payload, access_scope=AccessScope.from_user(current_user))
    publish_frontend_thing_update(entity)
    return repo.to_flat(entity)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestExternalMqttRepository = Depends(get_repo_ingest_external_mqtt),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
