from unittest.mock import MagicMock

from access_scope import AccessScope
from dependencies import get_repo_ingest
from repositories.ingest import IngestRepository

BASE_PATH = "/ingest"


def test_read_list_passes_superuser_access_scope(client, mock_user, override_repo):
    mock_user.is_superuser = True
    repo = override_repo(get_repo_ingest)
    repo.find_all.return_value = []

    response = client.get(f"{BASE_PATH}/")

    assert response.status_code == 200
    access_scope = repo.find_all.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_delete_passes_superuser_access_scope(client, mock_user, override_repo):
    mock_user.is_superuser = True
    repo = override_repo(get_repo_ingest)
    repo.delete.return_value = {"ok": True}

    response = client.delete(f"{BASE_PATH}/1")

    assert response.status_code == 200
    access_scope = repo.delete.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_find_all_does_not_filter_superuser_by_permission_group():
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalars.return_value.all.return_value = (
        []
    )
    repo = IngestRepository(session)

    repo.find_all(access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert statement.whereclause is None
