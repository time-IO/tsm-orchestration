from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
from models.filters import BaseFilter
from dependencies import (
    get_current_user,
    get_repo_parser_csv, max_file_size,
)
from models.parser import ParsedDataResponse
from models.parser_csv import (
    ParserCsvCreate,
    ParserCsvRead,
    ParserCsvUpdate,
)
from models import User
from repositories.parser_csv import ParserCsvRepository
from services.parse_data import parse_csv_data
from fastapi import File, Form, UploadFile
from access_scope import AccessScope

router = APIRouter(
    prefix="/parser/csv",
    tags=["parser/csv"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "csv parser"

BigPage = CustomizedPage[Page, UseParamsFields(size=500)]


@router.get(
    "/", response_model=BigPage[ParserCsvRead], summary=f"Get a list of {entity_name}"
)
def read_list(
    *,
    repo: ParserCsvRepository = Depends(get_repo_parser_csv),
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


@router.get("/{id}", response_model=ParserCsvRead, summary=f"Get one {entity_name}")
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: ParserCsvRepository = Depends(get_repo_parser_csv),
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
    parser_settings = ParserCsvUpdate.model_validate_json(settings)

    raw_data = (await file.read()).decode(parser_settings.encoding or 'UTF-8')

    response = parse_csv_data(
        settings=parser_settings,
        raw_data=raw_data,
    )

    return response


@router.post("/", response_model=ParserCsvRead, summary=f"Create one {entity_name}")
def create(
    *,
    payload: ParserCsvCreate,
    repo: ParserCsvRepository = Depends(get_repo_parser_csv),
    current_user: User = Depends(get_current_user),
):
    extra_data = {"created_by_id": current_user.id}
    return repo.to_flat(
        repo.create(
            payload, extra_data, access_scope=AccessScope.from_user(current_user)
        )
    )


@router.patch(
    "/{id}", summary=f"Update one {entity_name}", response_model=ParserCsvRead
)
def update(
    *,
    id: int,
    payload: ParserCsvUpdate,
    repo: ParserCsvRepository = Depends(get_repo_parser_csv),
    current_user: User = Depends(get_current_user),
):
    entity = repo.update(id, payload, access_scope=AccessScope.from_user(current_user))
    return repo.to_flat(entity)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: ParserCsvRepository = Depends(get_repo_parser_csv),
):
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))
