from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination import paginate
from dependencies import (
    get_current_user,
    get_repo_ingest_http,
    create_database_if_not_exists,
    get_repo_parser_detailed,
)
from models import User
from models.ingest_http import (
    IngestHttpCreate,
    IngestHttpUpdate,
    IngestHttpRead,
)
from models.filters import IngestFilter
from repositories.ingest_http import IngestHttpRepository
from repositories.parser_detailed import ParserDetailedRepository

from mqtt import publish_frontend_thing_update

router = APIRouter(
    prefix="/ingest/http",
    tags=["ingest/http"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest http"


@router.get(
    "/",
    response_model=Page[IngestHttpRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestHttpRepository = Depends(get_repo_ingest_http),
    filters: IngestFilter = Depends(),
    sort_by: str | None = None,
):
    return paginate(
        repo.find_all(current_user.permission_group_ids, sort_by, filters=filters)
    )


@router.get(
    "/{id}", response_model=IngestHttpRead, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestHttpRepository = Depends(get_repo_ingest_http),
):
    return repo.to_flat(
        repo.find_one(
            id, permission_group_ids_of_user=current_user.permission_group_ids
        )
    )


@router.post(
    "/",
    response_model=IngestHttpRead,
    summary=f"Create one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def create(
    *,
    payload: IngestHttpCreate,
    current_user: User = Depends(get_current_user),
    repo: IngestHttpRepository = Depends(get_repo_ingest_http),
    parser_repo: ParserDetailedRepository = Depends(get_repo_parser_detailed),
):
    if payload.parser_id:
        parser = parser_repo.find_one(
            payload.parser_id, current_user.permission_group_ids
        )
        if not parser or parser.permission_group_id != payload.permission_group_id:
            raise HTTPException(status_code=401, detail="Not allowed to use parser")

    # HTTP doesn't need SSH keypairs or bucket credentials like SFTP does
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
    response_model=IngestHttpRead,
    summary=f"Update one {entity_name}",
    dependencies=[Depends(create_database_if_not_exists)],
)
def update(
    *,
    id: int,
    payload: IngestHttpUpdate,
    current_user: User = Depends(get_current_user),
    repo: IngestHttpRepository = Depends(get_repo_ingest_http),
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
    repo: IngestHttpRepository = Depends(get_repo_ingest_http),
):
    return repo.delete(
        id, permission_group_ids_of_user=current_user.permission_group_ids
    )