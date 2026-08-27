from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
from models import User
from models.filters import BaseFilter
from dependencies import get_current_user, get_repo_parser_soilcan
from models.parser_soilcan import (
    ParserSoilcanCreate,
    ParserSoilcanRead,
    ParserSoilcanUpdate,
)

from repositories.parser_soilcan import ParserSoilcanRepository
from access_scope import AccessScope

router = APIRouter(
    prefix="/parser/soilcan",
    tags=["parser/soilcan"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "soilcan parser"

BigPage = CustomizedPage[Page, UseParamsFields(size=500)]


@router.get(
    "/",
    response_model=BigPage[ParserSoilcanRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    repo: ParserSoilcanRepository = Depends(get_repo_parser_soilcan),
    sort_by: str | None = None,
    current_user: User = Depends(get_current_user),
    filters: BaseFilter = Depends(),
):
    return paginate(
        repo.find_all(
            sort_by=sort_by,
            filters=filters,
            access_scope=AccessScope.from_user(current_user),
        )
    )


@router.get("/{id}", response_model=ParserSoilcanRead, summary=f"Get one {entity_name}")
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: ParserSoilcanRepository = Depends(get_repo_parser_soilcan),
):
    return repo.to_flat(
        repo.find_one(id, access_scope=AccessScope.from_user(current_user))
    )


@router.post("/", response_model=ParserSoilcanRead, summary=f"Create one {entity_name}")
def create(
    *,
    payload: ParserSoilcanCreate,
    repo: ParserSoilcanRepository = Depends(get_repo_parser_soilcan),
    current_user: User = Depends(get_current_user),
):
    extra_data = {"created_by_id": current_user.id}
    return repo.to_flat(
        repo.create(
            payload, extra_data, access_scope=AccessScope.from_user(current_user)
        )
    )


@router.patch(
    "/{id}", summary=f"Update one {entity_name}", response_model=ParserSoilcanRead
)
def update(
    *,
    id: int,
    payload: ParserSoilcanUpdate,
    repo: ParserSoilcanRepository = Depends(get_repo_parser_soilcan),
    current_user: User = Depends(get_current_user),
):
    entity = repo.update(id, payload, access_scope=AccessScope.from_user(current_user))
    return repo.to_flat(entity)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: ParserSoilcanRepository = Depends(get_repo_parser_soilcan),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
