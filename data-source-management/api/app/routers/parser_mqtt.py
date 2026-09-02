from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination import paginate
from dependencies import get_current_user, get_repo_parser_mqtt
from models.parser_mqtt import ParserMqttRead
from models.filters import ParserMqttFilter
from repositories.parser_mqtt import ParserMqttRepository

router = APIRouter(
    prefix="/parser/mqtt",
    tags=["parser/mqtt"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "mqtt-parser"


@router.get(
    "/", response_model=Page[ParserMqttRead], summary=f"Get a list of {entity_name}"
)
def read_list(
    *,
    repo: ParserMqttRepository = Depends(get_repo_parser_mqtt),
    filters: ParserMqttFilter = Depends(),
):
    return paginate(repo.find_all(filters=filters))


@router.get("/{id}", response_model=ParserMqttRead, summary=f"Get one {entity_name}")
def read_one(
    *,
    id: int,
    repo: ParserMqttRepository = Depends(get_repo_parser_mqtt),
):
    return repo.to_flat(repo.find_one(id))
