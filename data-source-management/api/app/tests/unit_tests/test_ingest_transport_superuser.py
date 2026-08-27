from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from access_scope import AccessScope
from repositories.ingest_external_sftp import IngestExternalSftpRepository
from repositories.ingest_mqtt import IngestMqttRepository
from repositories.ingest_sftp import IngestSftpRepository
from repositories.parser_detailed import ParserDetailedRepository
from routers import ingest_external_sftp, ingest_mqtt, ingest_sftp

ROUTER_CASES = (
    (ingest_external_sftp, IngestExternalSftpRepository),
    (ingest_mqtt, IngestMqttRepository),
    (ingest_sftp, IngestSftpRepository),
)
REPOSITORY_CLASSES = tuple(repository_class for _, repository_class in ROUTER_CASES)
SFTP_ROUTERS = (ingest_external_sftp, ingest_sftp)


class StopAfterAuthorization(Exception):
    pass


def _router_kwargs(router_module):
    if router_module in SFTP_ROUTERS:
        return {"parser_repo": MagicMock(spec=ParserDetailedRepository)}
    return {}


def _patch_generated_values(router_module, monkeypatch):
    monkeypatch.setattr(router_module, "generate_password", lambda length: "password")
    if router_module is ingest_external_sftp:
        monkeypatch.setattr(
            router_module, "generate_keypair", lambda: ("private-key", "public-key")
        )
    elif router_module is ingest_mqtt:
        monkeypatch.setattr(router_module, "hash_password", lambda value: "hash")


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
    router_module, repository_class, mock_user, monkeypatch
):
    mock_user.is_superuser = True
    repo = MagicMock(spec=repository_class)
    repo.create.return_value = object()
    monkeypatch.setattr(router_module, "publish_frontend_thing_update", MagicMock())
    _patch_generated_values(router_module, monkeypatch)
    payload = (
        SimpleNamespace(username=None)
        if router_module is ingest_mqtt
        else SimpleNamespace(parser_id=None)
    )

    router_module.create(
        payload=payload,
        current_user=mock_user,
        repo=repo,
        **_router_kwargs(router_module),
    )

    access_scope = repo.create.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


@pytest.mark.parametrize(("router_module", "repository_class"), ROUTER_CASES)
def test_update_passes_superuser_access_scope(
    router_module, repository_class, mock_user, monkeypatch
):
    mock_user.is_superuser = True
    repo = MagicMock(spec=repository_class)
    repo.update.return_value = object()
    monkeypatch.setattr(router_module, "publish_frontend_thing_update", MagicMock())
    payload = (
        object() if router_module is ingest_mqtt else SimpleNamespace(parser_id=None)
    )

    router_module.update(
        id=1,
        payload=payload,
        current_user=mock_user,
        repo=repo,
        **_router_kwargs(router_module),
    )

    access_scope = repo.update.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


@pytest.mark.parametrize("router_module", SFTP_ROUTERS)
def test_parser_lookup_passes_superuser_access_scope(
    router_module, mock_user, monkeypatch
):
    mock_user.is_superuser = True
    repo = MagicMock()
    repo.create.return_value = object()
    parser_repo = MagicMock(spec=ParserDetailedRepository)
    parser_repo.find_one.return_value = SimpleNamespace(permission_group_id=999)
    monkeypatch.setattr(router_module, "publish_frontend_thing_update", MagicMock())
    _patch_generated_values(router_module, monkeypatch)
    payload = SimpleNamespace(parser_id=1, permission_group_id=999)

    router_module.create(
        payload=payload,
        current_user=mock_user,
        repo=repo,
        parser_repo=parser_repo,
    )

    access_scope = parser_repo.find_one.call_args.kwargs["access_scope"]
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
def test_update_accepts_superuser_permission_group(repository_class):
    repo = repository_class(MagicMock())
    repo.find_one = MagicMock(side_effect=StopAfterAuthorization)
    payload = SimpleNamespace(permission_group_id=999)
    access_scope = AccessScope([], is_superuser=True)

    with pytest.raises(StopAfterAuthorization):
        repo.update(1, payload, access_scope=access_scope)

    repo.find_one.assert_called_once_with(1, access_scope=access_scope)


@pytest.mark.parametrize("repository_class", REPOSITORY_CLASSES)
def test_create_keeps_permission_group_check(repository_class):
    repo = repository_class(MagicMock())
    payload = SimpleNamespace(permission_group_id=999, name="test")

    with pytest.raises(HTTPException) as exc_info:
        repo.create(payload, {}, AccessScope([1]))

    assert exc_info.value.status_code == 403


@pytest.mark.parametrize("repository_class", REPOSITORY_CLASSES)
def test_update_keeps_permission_group_check(repository_class):
    repo = repository_class(MagicMock())
    payload = SimpleNamespace(permission_group_id=999)

    with pytest.raises(HTTPException) as exc_info:
        repo.update(1, payload, AccessScope([1]))

    assert exc_info.value.status_code == 403


def test_parser_find_one_does_not_filter_superuser_by_permission_group():
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalar_one_or_none.return_value = (
        object()
    )
    repo = ParserDetailedRepository(session)

    repo.find_one(1, access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert "permission_group_id IN" not in str(statement)
