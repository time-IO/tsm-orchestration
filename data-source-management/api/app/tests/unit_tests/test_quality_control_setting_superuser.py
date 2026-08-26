from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from access_scope import AccessScope
from models import QualityControlSettingRepository
from routers import quality_control_setting


class StopAfterAuthorization(Exception):
    pass


def test_read_list_passes_superuser_access_scope(mock_user, monkeypatch):
    mock_user.is_superuser = True
    repo = MagicMock(spec=QualityControlSettingRepository)
    repo.find_allowed_all.return_value = []
    monkeypatch.setattr(quality_control_setting, "paginate", lambda items: items)

    quality_control_setting.read_list(
        current_user=mock_user, repo=repo, filters=None, sort_by=None
    )

    access_scope = repo.find_allowed_all.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_read_one_passes_superuser_access_scope(mock_user):
    mock_user.is_superuser = True
    repo = MagicMock(spec=QualityControlSettingRepository)
    repo.find_allowed_one.return_value = object()

    quality_control_setting.read_one(id=1, current_user=mock_user, repo=repo)

    access_scope = repo.find_allowed_one.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_create_passes_superuser_access_scope(mock_user, monkeypatch):
    mock_user.is_superuser = True
    repo = MagicMock(spec=QualityControlSettingRepository)
    repo.create_allowed.return_value = object()
    monkeypatch.setattr(
        quality_control_setting, "publish_qaqc_settings_update", MagicMock()
    )
    payload = SimpleNamespace(quality_control_functions=[])

    quality_control_setting.create(payload=payload, current_user=mock_user, repo=repo)

    access_scope = repo.create_allowed.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_update_passes_superuser_access_scope(mock_user, monkeypatch):
    mock_user.is_superuser = True
    repo = MagicMock(spec=QualityControlSettingRepository)
    repo.update_allowed.return_value = object()
    monkeypatch.setattr(
        quality_control_setting, "publish_qaqc_settings_update", MagicMock()
    )
    payload = SimpleNamespace(quality_control_functions=None)

    quality_control_setting.update(
        id=1, payload=payload, current_user=mock_user, repo=repo
    )

    access_scope = repo.update_allowed.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_delete_passes_superuser_access_scope(mock_user):
    mock_user.is_superuser = True
    repo = MagicMock(spec=QualityControlSettingRepository)
    repo.delete_allowed.return_value = {"ok": True}

    quality_control_setting.delete(id=1, current_user=mock_user, repo=repo)

    access_scope = repo.delete_allowed.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_find_allowed_all_does_not_filter_superuser_by_permission_group():
    session = MagicMock()
    session.exec.return_value.unique.return_value.all.return_value = []
    repo = QualityControlSettingRepository(session)

    repo.find_allowed_all(access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert statement.whereclause is None


def test_find_allowed_one_does_not_filter_superuser_by_permission_group():
    session = MagicMock()
    session.exec.return_value.first.return_value = object()
    repo = QualityControlSettingRepository(session)

    repo.find_allowed_one(1, access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert "permission_group_id IN" not in str(statement)


def test_delete_passes_access_scope_to_find_allowed_one():
    session = MagicMock()
    repo = QualityControlSettingRepository(session)
    entity = object()
    repo.find_allowed_one = MagicMock(return_value=entity)
    access_scope = AccessScope([], is_superuser=True)

    assert repo.delete_allowed(1, access_scope) == {"ok": True}

    repo.find_allowed_one.assert_called_once_with(1, access_scope=access_scope)
    session.delete.assert_called_once_with(entity)
    session.commit.assert_called_once_with()


def test_find_allowed_all_filters_by_access_scope():
    session = MagicMock()
    session.exec.return_value.unique.return_value.all.return_value = []
    repo = QualityControlSettingRepository(session)

    repo.find_allowed_all(access_scope=AccessScope([1]))

    statement = session.exec.call_args.args[0]
    assert statement.whereclause is not None


def test_create_accepts_superuser_permission_group():
    repo = QualityControlSettingRepository(MagicMock())
    repo.check_for_existing_name = MagicMock(side_effect=StopAfterAuthorization)
    payload = SimpleNamespace(permission_group_id=999, name="test")

    with pytest.raises(StopAfterAuthorization):
        repo.create_allowed(
            payload, {}, access_scope=AccessScope([], is_superuser=True)
        )


def test_create_checks_access_scope_permission_groups():
    repo = QualityControlSettingRepository(MagicMock())
    payload = SimpleNamespace(permission_group_id=999, name="test")

    with pytest.raises(HTTPException) as exc_info:
        repo.create_allowed(payload, {}, access_scope=AccessScope([1]))

    assert exc_info.value.status_code == 403


def test_update_passes_superuser_scope_to_find_allowed_one():
    repo = QualityControlSettingRepository(MagicMock())
    repo.find_allowed_one = MagicMock(side_effect=HTTPException(status_code=418))
    payload = MagicMock()
    payload.permission_group_id = 999
    payload.model_dump.return_value = {}
    access_scope = AccessScope([], is_superuser=True)

    with pytest.raises(HTTPException) as exc_info:
        repo.update_allowed(1, payload, access_scope=access_scope)

    assert exc_info.value.status_code == 418
    repo.find_allowed_one.assert_called_once_with(1, access_scope=access_scope)


def test_update_checks_access_scope_permission_groups():
    repo = QualityControlSettingRepository(MagicMock())
    payload = MagicMock()
    payload.permission_group_id = 999

    with pytest.raises(HTTPException) as exc_info:
        repo.update_allowed(1, payload, access_scope=AccessScope([1]))

    assert exc_info.value.status_code == 403
