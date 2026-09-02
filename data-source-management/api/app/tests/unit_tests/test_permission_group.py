from unittest.mock import MagicMock
from uuid import UUID

from access_scope import AccessScope
from dependencies import get_repo_permission_group
from models import PermissionGroupRepository

BASE_PATH = "/permission-group"


def test_read_list_passes_superuser_access_scope(client, mock_user, override_repo):
    mock_user.is_superuser = True
    repo = override_repo(get_repo_permission_group)
    repo.find_allowed_all.return_value = []

    response = client.get(f"{BASE_PATH}/")

    assert response.status_code == 200
    access_scope = repo.find_allowed_all.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_read_one_passes_superuser_access_scope(client, mock_user, override_repo):
    mock_user.is_superuser = True
    repo = override_repo(get_repo_permission_group)
    repo.find_allowed_one.return_value = {
        "id": 1,
        "name": "Permission Group",
        "uuid": UUID("00000000-0000-0000-0000-000000000001"),
        "entitlement": "urn:test:group:1",
    }

    response = client.get(f"{BASE_PATH}/1")

    assert response.status_code == 200
    access_scope = repo.find_allowed_one.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_find_allowed_all_does_not_filter_superuser_by_membership():
    session = MagicMock()
    session.exec.return_value.all.return_value = []
    repo = PermissionGroupRepository(session)

    repo.find_allowed_all(access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert statement.whereclause is None
