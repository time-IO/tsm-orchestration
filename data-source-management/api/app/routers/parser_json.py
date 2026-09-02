from fastapi import APIRouter, Depends, Form
from fastapi_pagination import Page, paginate
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
from models import User
from models.filters import BaseFilter
from dependencies import get_current_user, get_repo_parser_json, max_file_size
from models.parser import ParsedDataResponse
from models.parser_json import (
    ParserJsonCreate,
    ParserJsonRead,
    ParserJsonUpdate,
)

from repositories.parser_json import ParserJsonRepository
from services.parse_data import parse_json_data
from fastapi import File, Form, UploadFile
from access_scope import AccessScope

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
            filters=filters,
            access_scope=AccessScope.from_user(current_user),
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
        repo.find_one(id, access_scope=AccessScope.from_user(current_user))
    )


@router.post(
    "/parse",
    response_model=ParsedDataResponse,
    summary=f"Parse a file with a given {entity_name}",
)
async def validate(
    settings: str = Form(...),
    file: UploadFile = Depends(max_file_size(1024 * 1024)),
) -> ParsedDataResponse:
    parser_settings = ParserJsonUpdate.model_validate_json(settings)

    raw_data = (await file.read()).decode("utf-8")  # TODO assume utf-8?

    response = parse_json_data(
        settings=parser_settings,
        raw_data=raw_data,
    )

    return response


@router.post("/", response_model=ParserJsonRead, summary=f"Create one {entity_name}")
def create(
    *,
    payload: ParserJsonCreate,
    repo: ParserJsonRepository = Depends(get_repo_parser_json),
    current_user: User = Depends(get_current_user),
):
    extra_data = {"created_by_id": current_user.id}
    return repo.to_flat(
        repo.create(
            payload, extra_data, access_scope=AccessScope.from_user(current_user)
        )
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
    entity = repo.update(id, payload, access_scope=AccessScope.from_user(current_user))
    return repo.to_flat(entity)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: ParserJsonRepository = Depends(get_repo_parser_json),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
