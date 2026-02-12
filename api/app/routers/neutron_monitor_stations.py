from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ..models.neutron_monitor_stations import NeutronMonitorStations
from ..dependencies import get_session, get_current_user

router = APIRouter(
    prefix="/neutron-monitor-stations",
    tags=["neutron-monitor-stations"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "neutron monitor station"


@router.get(
    "/",
    response_model=list[NeutronMonitorStations],
    summary=f"Get a list of {entity_name}",
)
def read_list(*, session: Session = Depends(get_session)):
    entities = session.exec(select(NeutronMonitorStations)).all()
    return entities


@router.get(
    "/{id}", response_model=NeutronMonitorStations, summary=f"Get one {entity_name}"
)
def read_one(*, session: Session = Depends(get_session), id: int):
    entity = session.get(NeutronMonitorStations, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity
