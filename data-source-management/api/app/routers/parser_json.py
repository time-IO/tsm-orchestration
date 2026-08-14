from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
from models import User
from models.filters import BaseFilter
from dependencies import get_current_user, get_repo_parser_json
from models.parser_json import (
    ParserJsonCreate,
    ParserJsonRead,
    ParserJsonUpdate,
)

from repositories.parser_json import ParserJsonRepository

router = APIRouter(
    prefix="/parser/json",
    tags=["parser/json"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "json parser"

BigPage = CustomizedPage[Page, UseParamsFields(size=500)]


@router.get(
    "/", response_model=BigPage[ParserJsonRead], summary=f"Get a list of {entity_name}"
)
def read_list(
    *,
    repo: ParserJsonRepository = Depends(get_repo_parser_json),
    sort_by: str | None = None,
    current_user: User = Depends(get_current_user),
    filters: BaseFilter = Depends(),
):
    return paginate(
        repo.find_all(
            sort_by=sort_by,
            permission_group_ids_of_user=current_user.permission_group_ids,
            filters=filters,
        )
    )


@router.get("/{id}", response_model=ParserJsonRead, summary=f"Get one {entity_name}")
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: ParserJsonRepository = Depends(get_repo_parser_json),
):
    return repo.to_flat(
        repo.find_one(
            id, permission_group_ids_of_user=current_user.permission_group_ids
        )
    )


@router.post("/", response_model=ParserJsonRead, summary=f"Create one {entity_name}")
def create(
    *,
    payload: ParserJsonCreate,
    repo: ParserJsonRepository = Depends(get_repo_parser_json),
    current_user: User = Depends(get_current_user),
):
    extra_data = {"created_by_id": current_user.id}
    return repo.to_flat(
        repo.create(payload, extra_data, current_user.permission_group_ids)
    )


@router.patch(
    "/{id}", summary=f"Update one {entity_name}", response_model=ParserJsonRead
)
def update(
    *,
    id: int,
    payload: ParserJsonUpdate,
    repo: ParserJsonRepository = Depends(get_repo_parser_json),
    current_user: User = Depends(get_current_user),
):
    entity = repo.update(
        id, payload, permission_group_ids_of_user=current_user.permission_group_ids
    )
    return repo.to_flat(entity)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: ParserJsonRepository = Depends(get_repo_parser_json),
):
    return repo.delete(
        id, permission_group_ids_of_user=current_user.permission_group_ids
    )
