from fastapi import APIRouter, HTTPException

from ..models.mqtt_parser import MqttParser

router = APIRouter(
    prefix="/mqtt-parser",
    tags= ["mqtt-parser"],
    responses={404: {"description": "Not found"}},
)

entity_name = "mqtt-parser"

list_of_mqtt_parser = {
1:{"id":1, "name":"Campbell CR6"},
2:{"id":2, "name":"Schlumberger"},
3:{"id":3, "name":"campbell_cr6"},
4:{"id":4, "name":"brightsky_dwd_api"},
5:{"id":5, "name":"ydoc_ml417"},
6:{"id":6, "name":"sine_dummy"},
7:{"id":7, "name":"Gude"}
}
@router.get("/", response_model=list[MqttParser], summary=f"Get a list of {entity_name}")
def read_list():
    return list_of_mqtt_parser.values()

@router.get("/{id}", response_model=MqttParser, summary=f"Get one {entity_name}")
def read_one(id: int):
    entity = list_of_mqtt_parser.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity