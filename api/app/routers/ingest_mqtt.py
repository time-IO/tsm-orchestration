from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..dependencies import get_session, get_current_user
from ..models.ingest_mqtt import (
    IngestMqttCreate,
    IngestMqttPublic,
    IngestMqttUpdate,
    IngestMqtt,
)

router = APIRouter(
    prefix="/ingest/mqtt",
    tags=["ingest/mqtt"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest mqtt"


@router.get(
    "/", response_model=list[IngestMqttPublic], summary=f"Get a list of {entity_name}"
)
def read_list(*, session: Session = Depends(get_session)):
    entities = session.exec(select(IngestMqtt)).all()
    return entities


@router.get("/{id}", response_model=IngestMqttPublic, summary=f"Get one {entity_name}")
def read_one(*, session: Session = Depends(get_session), id: int):
    entity = session.get(IngestMqtt, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity


@router.post("/", response_model=IngestMqttPublic, summary=f"Create one {entity_name}")
def create(
    *,
    session: Session = Depends(get_session),
    payload: IngestMqttCreate,
    user=Depends(get_current_user),
):

    extra_data = {"created_by_id": user.id}

    # todo username
    # todo password (encrypted)
    # todo password_hashed (encrypted)
    # todo uri

    entity = IngestMqtt.model_validate(payload, update=extra_data)
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


@router.patch(
    "/{id}", response_model=IngestMqttPublic, summary=f"Update one {entity_name}"
)
def update(
    *, session: Session = Depends(get_session), id: int, payload: IngestMqttUpdate
):
    entity = session.get(IngestMqtt, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    data = payload.model_dump(exclude_unset=True)
    entity.sqlmodel_update(data)
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(*, session: Session = Depends(get_session), id: int):
    entity = session.get(IngestMqtt, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    session.delete(entity)
    session.commit()
    return {"ok": True}
