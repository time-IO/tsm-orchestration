from typing import Literal

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from dependencies import get_current_user, get_repo_parser_predefined
from models.parser_predefined import ParserPredefinedRead
from models.filters.parser_predefined import ParserPredefinedFilter
from repositories.parser_predefined import ParserPredefinedRepository

router = APIRouter(
    prefix="/parser/predefined",
    tags=["parser/predefined"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=Page[ParserPredefinedRead])
def read_list(
    repo: ParserPredefinedRepository = Depends(get_repo_parser_predefined),
    filters: ParserPredefinedFilter = Depends(),
    recommended_for: Literal["file", "mqtt"] | None = None,
):
    # Recommendations only affect selection lists. All records remain readable
    # and selectable through the API regardless of their usual transport.
    repo.recommended_for = recommended_for
    return paginate(repo.find_all(filters=filters))


@router.get("/{id}", response_model=ParserPredefinedRead)
def read_one(
    id: int,
    repo: ParserPredefinedRepository = Depends(get_repo_parser_predefined),
):
    return repo.find_one(id)
