from fastapi import APIRouter, Depends
from dependencies import get_current_user, get_repo_mqtt_parser
from models.parser_mqtt import MqttParser

router = APIRouter(
    prefix="/mqtt-parser",
    tags=["mqtt-parser"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "mqtt-parser"


@router.get(
    "/", response_model=list[MqttParser], summary=f"Get a list of {entity_name}"
)
def read_list(
    *,
    repo=Depends(get_repo_mqtt_parser),
):
    return repo.find_all()


@router.get("/{id}", response_model=MqttParser, summary=f"Get one {entity_name}")
def read_one(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_mqtt_parser),
):
    return repo.find_one(id, current_user.permission_group_ids)
