from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from access_scope import AccessScope
from repositories.parser_csv import ParserCsvRepository
from repositories.parser_json import ParserJsonRepository
from repositories.parser_soilcan import ParserSoilcanRepository
from routers import parser_csv, parser_json, parser_soilcan

ROUTER_CASES = (
    (parser_csv, ParserCsvRepository),
    (parser_json, ParserJsonRepository),
    (parser_soilcan, ParserSoilcanRepository),
)
REPOSITORY_CLASSES = tuple(repository_class for _, repository_class in ROUTER_CASES)
TIMESTAMP_REPOSITORY_CASES = (
    (ParserCsvRepository, "update_timestamp_columns"),
    (ParserJsonRepository, "update_timestamp_keys"),
)


class StopAfterAuthorization(Exception):
    pass


@pytest.mark.parametrize(("router_module", "repository_class"), ROUTER_CASES)
def test_read_list_passes_superuser_access_scope(
    router_module, repository_class, mock_user, monkeypatch
):
    mock_user.is_superuser = True
    repo = MagicMock(spec=repository_class)
    repo.find_all.return_value = []
    monkeypatch.setattr(router_module, "paginate", lambda items: items)

    router_module.read_list(current_user=mock_user, repo=repo)

    access_scope = repo.find_all.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


@pytest.mark.parametrize(("router_module", "repository_class"), ROUTER_CASES)
def test_read_one_passes_superuser_access_scope(
    router_module, repository_class, mock_user
):
    mock_user.is_superuser = True
    repo = MagicMock(spec=repository_class)
    repo.find_one.return_value = object()

    router_module.read_one(id=1, current_user=mock_user, repo=repo)

    access_scope = repo.find_one.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


@pytest.mark.parametrize(("router_module", "repository_class"), ROUTER_CASES)
def test_create_passes_superuser_access_scope(
    router_module, repository_class, mock_user
):
    mock_user.is_superuser = True
    repo = MagicMock(spec=repository_class)
    repo.create.return_value = object()

    router_module.create(payload=object(), current_user=mock_user, repo=repo)

    access_scope = repo.create.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


@pytest.mark.parametrize(("router_module", "repository_class"), ROUTER_CASES)
def test_update_passes_superuser_access_scope(
    router_module, repository_class, mock_user
):
    mock_user.is_superuser = True
    repo = MagicMock(spec=repository_class)
    repo.update.return_value = object()

    router_module.update(id=1, payload=object(), current_user=mock_user, repo=repo)

    access_scope = repo.update.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


@pytest.mark.parametrize("repository_class", REPOSITORY_CLASSES)
def test_find_all_does_not_filter_superuser_by_permission_group(repository_class):
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalars.return_value.all.return_value = (
        []
    )
    repo = repository_class(session)

    repo.find_all(access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert statement.whereclause is None


@pytest.mark.parametrize("repository_class", REPOSITORY_CLASSES)
def test_find_one_does_not_filter_superuser_by_permission_group(repository_class):
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalar_one_or_none.return_value = (
        object()
    )
    repo = repository_class(session)

    repo.find_one(1, access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert "permission_group_id IN" not in str(statement)


@pytest.mark.parametrize("repository_class", REPOSITORY_CLASSES)
def test_find_all_keeps_permission_group_filter(repository_class):
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalars.return_value.all.return_value = (
        []
    )
    repo = repository_class(session)

    repo.find_all(AccessScope([1]))

    statement = session.exec.call_args.args[0]
    assert statement.whereclause is not None


@pytest.mark.parametrize("repository_class", REPOSITORY_CLASSES)
def test_create_accepts_superuser_permission_group(repository_class):
    repo = repository_class(MagicMock())
    repo.check_for_existing_name_create = MagicMock(side_effect=StopAfterAuthorization)
    payload = SimpleNamespace(permission_group_id=999, name="test")

    with pytest.raises(StopAfterAuthorization):
        repo.create(payload, {}, access_scope=AccessScope([], is_superuser=True))


@pytest.mark.parametrize("repository_class", REPOSITORY_CLASSES)
def test_create_keeps_permission_group_check(repository_class):
    repo = repository_class(MagicMock())
    payload = SimpleNamespace(permission_group_id=999, name="test")

    with pytest.raises(HTTPException) as exc_info:
        repo.create(payload, {}, AccessScope([1]))

    assert exc_info.value.status_code == 403


@pytest.mark.parametrize("repository_class", REPOSITORY_CLASSES)
def test_update_passes_superuser_scope_to_find_one(repository_class):
    repo = repository_class(MagicMock())
    repo.find_one = MagicMock(side_effect=StopAfterAuthorization)
    payload = MagicMock()
    payload.timestamp_columns = None
    payload.timestamp_keys = None
    payload.model_dump.return_value = {}
    access_scope = AccessScope([], is_superuser=True)

    with pytest.raises(StopAfterAuthorization):
        repo.update(1, payload, access_scope=access_scope)

    repo.find_one.assert_called_once_with(1, access_scope=access_scope)


@pytest.mark.parametrize("repository_class", REPOSITORY_CLASSES)
def test_update_keeps_permission_group_scope(repository_class):
    repo = repository_class(MagicMock())
    repo.find_one = MagicMock(side_effect=StopAfterAuthorization)
    payload = MagicMock()
    payload.timestamp_columns = None
    payload.timestamp_keys = None
    payload.model_dump.return_value = {}

    with pytest.raises(StopAfterAuthorization):
        repo.update(1, payload, AccessScope([1]))

    access_scope = repo.find_one.call_args.kwargs["access_scope"]
    assert access_scope == AccessScope([1])


@pytest.mark.parametrize(
    ("repository_class", "timestamp_update_method"), TIMESTAMP_REPOSITORY_CASES
)
def test_update_checks_access_before_updating_timestamps(
    repository_class, timestamp_update_method
):
    repo = repository_class(MagicMock())
    repo.find_one = MagicMock(side_effect=StopAfterAuthorization)
    update_timestamps = MagicMock()
    setattr(repo, timestamp_update_method, update_timestamps)

    with pytest.raises(StopAfterAuthorization):
        repo.update(1, MagicMock(), AccessScope([1]))

    update_timestamps.assert_not_called()
