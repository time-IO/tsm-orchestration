from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination import paginate
from dependencies import get_current_user, get_repo_neutron_monitor_station
from models.neutron_monitor_station import NeutronMonitorStation

router = APIRouter(
    prefix="/neutron-monitor-station",
    tags=["neutron-monitor-station"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "neutron monitor station"


@router.get(
    "/",
    response_model=Page[NeutronMonitorStation],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    repo=Depends(get_repo_neutron_monitor_station),
):
    return paginate(repo.find_all())


@router.get(
    "/{id}", response_model=NeutronMonitorStation, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    repo=Depends(get_repo_neutron_monitor_station),
):
    return repo.find_one(id)
