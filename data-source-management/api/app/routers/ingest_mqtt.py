from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination import paginate
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_mqtt,
    create_database_if_not_exists,
)
from models import User
from models.ingest_mqtt import (
    IngestMqttCreate,
    IngestMqttRead,
)
from models.ingest import IngestUpdate
from models.filters import IngestFilter
import uuid
import re

from config import settings

from repositories.ingest_mqtt import IngestMqttRepository
from utils import generate_password, hash_password

from mqtt import publish_frontend_thing_update

router = APIRouter(
    prefix="/ingest/mqtt",
    tags=["ingest/mqtt"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest mqtt"


def normalize_mqtt_username(username: str) -> str:
    return username.strip().lower()


@router.get(
    "/", response_model=Page[IngestMqttRead], summary=f"Get a list of {entity_name}"
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestMqttRepository = Depends(get_repo_ingest_mqtt),
    filters: IngestFilter = Depends(),
    sort_by: str | None = None,
):
    return paginate(
        repo.find_all(
            sort_by=sort_by,
            filters=filters,
            access_scope=AccessScope.from_user(current_user),
        )
    )


@router.get("/{id}", response_model=IngestMqttRead, summary=f"Get one {entity_name}")
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestMqttRepository = Depends(get_repo_ingest_mqtt),
):
    return repo.to_flat(
        repo.find_one(id, access_scope=AccessScope.from_user(current_user))
    )


@router.post(
    "/",
    response_model=IngestMqttRead,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestMqttCreate,
    current_user: User = Depends(get_current_user),
    repo: IngestMqttRepository = Depends(get_repo_ingest_mqtt),
):
    _uuid = uuid.uuid4()

    password = generate_password(40)
    password_hashed = hash_password(password)
    if payload.username:
        username = normalize_mqtt_username(payload.username)
        if len(username) < 8:
            raise HTTPException(
                status_code=400,
                detail="MQTT username must be at least 8 characters long.",
            )
        if not re.fullmatch(r"[a-z0-9-]+", username):
            raise HTTPException(
                status_code=400,
                detail="MQTT username may only contain lowercase letters, numbers, and hyphens.",
            )
    else:
        username = re.sub("[^a-z0-9-]+", "", f"ingest-mqtt-{_uuid}")

    topic = "mqtt_ingest/" + username

    extra_data = {
        "created_by_id": current_user.id,
        "password": password,
        "password_hashed": password_hashed,
        "username": username,
        "uuid": _uuid,
        "topic": topic,
        "uri": settings.INGEST_MQTT_BROKER_URI,
    }

    entity = repo.create(
        payload,
        extra_data,
        access_scope=AccessScope.from_user(current_user),
    )
    publish_frontend_thing_update(entity)
    return repo.to_flat(entity)


@router.patch(
    "/{id}",
    response_model=IngestMqttRead,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestUpdate,
    current_user: User = Depends(get_current_user),
    repo: IngestMqttRepository = Depends(get_repo_ingest_mqtt),
):
    entity = repo.update(id, payload, access_scope=AccessScope.from_user(current_user))
    publish_frontend_thing_update(entity)
    return repo.to_flat(entity)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestMqttRepository = Depends(get_repo_ingest_mqtt),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
