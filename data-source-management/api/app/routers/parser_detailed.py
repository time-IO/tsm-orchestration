from fastapi import APIRouter, Depends
from access_scope import AccessScope
from dependencies import get_current_user, get_repo_parser_detailed

from fastapi_pagination import Page
from fastapi_pagination import paginate
from models import User
from models.filters import ParserDetailedFilter

from models.parser_detailed import ParserDetailedRead
from repositories.parser_detailed import ParserDetailedRepository

router = APIRouter(
    prefix="/parser-detailed",
    tags=["parser-detailed"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "parser-detailed"


@router.get(
    "/",
    response_model=Page[ParserDetailedRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: ParserDetailedRepository = Depends(get_repo_parser_detailed),
    filters: ParserDetailedFilter = Depends(),
    sort_by: str | None = None,
):
    return paginate(
        repo.find_all(AccessScope.from_user(current_user), sort_by, filters=filters)
    )


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: ParserDetailedRepository = Depends(get_repo_parser_detailed),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
