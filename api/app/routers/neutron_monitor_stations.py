from fastapi import APIRouter, Depends
from ..models.neutron_monitor_stations import NeutronMonitorStations
from ..dependencies import get_current_user, get_repo_neutron_monitor_stations

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
def read_list(
    *,
    repo=Depends(get_repo_neutron_monitor_stations),
):
    return repo.find_all()


@router.get(
    "/{id}", response_model=NeutronMonitorStations, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_neutron_monitor_stations),
):
    return repo.find_one(id, current_user.permission_group_ids)
