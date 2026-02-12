from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ..dependencies import get_session, get_current_user
from ..models.mqtt_parser import MqttParser

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
def read_list(*, session: Session = Depends(get_session)):
    entities = session.exec(select(MqttParser)).all()
    return entities


@router.get("/{id}", response_model=MqttParser, summary=f"Get one {entity_name}")
def read_one(*, session: Session = Depends(get_session), id: int):
    entity = session.get(MqttParser, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity
