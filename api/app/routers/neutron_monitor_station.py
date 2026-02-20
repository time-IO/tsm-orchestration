from fastapi import APIRouter, Depends
from models.neutron_monitor_station import NeutronMonitorStation
from models.user import User
from models.base_repository import BaseRepository
from dependencies import get_current_user, get_repo_neutron_monitor_station

router = APIRouter(
    prefix="/neutron-monitor-station",
    tags=["neutron-monitor-station"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "neutron monitor station"


@router.get(
    "/",
    response_model = list[NeutronMonitorStation],
    summary = f"Get a list of {entity_name}",
)
def read_list(
    *,
    repo: BaseRepository = Depends(get_repo_neutron_monitor_station),
):
    return repo.find_all()


@router.get(
    "/{id}", response_model=NeutronMonitorStation, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: BaseRepository = Depends(get_repo_neutron_monitor_station),
):
    return repo.find_one(id, current_user.permission_group_ids)
