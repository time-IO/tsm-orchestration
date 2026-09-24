import pytest

from dependencies import get_repo_neutron_monitor_station
from models.neutron_monitor_station import NeutronMonitorStation

BASE_PATH = "/neutron-monitor-station"


def test_read_list_returns_global_station_catalog_for_superuser(
    client, mock_user, override_repo
):
    mock_user.is_superuser = True
    repo = override_repo(get_repo_neutron_monitor_station)
    repo.find_all.return_value = []

    response = client.get(f"{BASE_PATH}/")

    assert response.status_code == 200
    repo.find_all.assert_called_once_with()


@pytest.mark.parametrize("is_superuser", [False, True])
def test_read_one_returns_global_station_for_all_authenticated_users(
    client, mock_user, override_repo, is_superuser
):
    mock_user.is_superuser = is_superuser
    repo = override_repo(get_repo_neutron_monitor_station)
    repo.find_one.return_value = NeutronMonitorStation(
        id=1,
        station_id="TEST",
        description="Test station",
    )

    response = client.get(f"{BASE_PATH}/1")

    assert response.status_code == 200
    repo.find_one.assert_called_once_with(1)
