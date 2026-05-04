from fastapi import APIRouter, Depends
from dependencies import (
    get_current_user,
    get_repo_ingest,
)
from models import User
from models.filters import IngestFilter
from models.ingest import IngestWithApiInfoRead
from repositories.ingest import IngestRepository

from fastapi_pagination import Page
from fastapi_pagination import paginate

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
    return paginate(
        repo.find_all(current_user.permission_group_ids, sort_by, filters=filters)
    )


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestRepository = Depends(get_repo_ingest),
):
    return repo.delete(
        id, permission_group_ids_of_user=current_user.permission_group_ids
    )
