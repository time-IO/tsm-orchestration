from fastapi import APIRouter, Depends
from dependencies import get_current_user, get_repo_ingest_mqtt
from models.ingest_mqtt import (
    IngestMqttCreate,
    IngestMqttPublic,
    IngestMqttUpdate,
)
import os
import hashlib
import base64
import string
import secrets
import uuid
import re

router = APIRouter(
    prefix="/ingest/mqtt",
    tags=["ingest/mqtt"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest mqtt"


def hash_password(
    password: str,
    hasher: str = "pbkdf2_sha256",
    iterations: int = 260000,
    salt: bytes = None,
) -> str:
    """
    Hash a password using PBKDF2 (equivalent to Django's make_password with PBKDF2 hasher).

    Returns a string in Django-compatible format: 'algorithm$iterations$salt$hash'
    """
    if hasher != "pbkdf2_sha256":
        raise ValueError("Only 'pbkdf2_sha256' is supported in this implementation")

    if salt is None:
        salt = os.urandom(16)  # Django uses 16-byte random salt

    # Ensure password is bytes
    password_bytes = password.encode("utf-8")

    # PBKDF2-HMAC-SHA256
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, iterations)

    # Encode salt and hash in base64 (Django uses base64 without padding)
    salt_b64 = base64.b64encode(salt).rstrip(b"=").decode("ascii")
    hash_b64 = base64.b64encode(hash_bytes).rstrip(b"=").decode("ascii")

    return f"pbkdf2_sha256${iterations}${salt_b64}${hash_b64}"


def generate_password(length: int):
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


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

    _uuid = uuid.uuid4()

    password = generate_password(40)
    password_hashed = hash_password(password)
    username = re.sub("[^a-z0-9-]+", "", f"ingest-mqtt-{_uuid}")

    extra_data = {
        "created_by_id": current_user.id,
        "password": password,
        "password_hashed": password_hashed,
        "username": username,
        "uuid": _uuid,
    }

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
