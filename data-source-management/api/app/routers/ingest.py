from fastapi import APIRouter, Depends
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest,
)
from models import User
from models.filters import IngestFilter
from models.ingest import IngestWithApiInfoRead
from repositories.ingest import IngestRepository
import logging

from fastapi_pagination import Page
from fastapi_pagination import paginate

logger = logging.getLogger("app.routers.ingest")

router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest"


@router.get(
    "/",
    response_model=Page[IngestWithApiInfoRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestRepository = Depends(get_repo_ingest),
    filters: IngestFilter = Depends(),
    sort_by: str | None = None,
):
    logger.debug(
        "List ingest requested by user_id=%s sort_by=%s filters=%s",
        current_user.id,
        sort_by,
        filters,
    )
    return paginate(
        repo.find_all(
            sort_by=sort_by,
            filters=filters,
            access_scope=AccessScope.from_user(current_user),
        )
    )


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestRepository = Depends(get_repo_ingest),
):
    logger.debug(
        "Delete ingest requested by user_id=%s ingest_id=%s", current_user.id, id
    )
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
