from fastapi import APIRouter, Depends
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_external_api,
)
from models import User
from models.filters import IngestExternalApiFilter
from models.ingest_external_api import IngestExternalApiRead

from repositories.ingest import IngestRepository

from fastapi_pagination import Page
from fastapi_pagination import paginate

router = APIRouter(
    prefix="/ingest/external-api",
    tags=["ingest/external-api"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external api"


@router.get(
    "/",
    response_model=Page[IngestExternalApiRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestRepository = Depends(get_repo_ingest_external_api),
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
