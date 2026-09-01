import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from access_scope import AccessScope
from models import TriggerQualityControl, TriggerSyncExtApiBase, TriggerSyncExtSftpBase
from repositories.ingest import IngestRepository
from routers import (
    sta_proxy,
    trigger_ext_api,
    trigger_ext_sftp,
    trigger_quality_control,
)
from services import trigger_ext_api as trigger_ext_api_service_module
from services import trigger_ext_sftp as trigger_ext_sftp_service_module
from services import trigger_quality_control as trigger_quality_control_service_module


class FakeStaResponse:
    def json(self):
        return {"ok": True}


class FakeAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def get(self, url):
        return FakeStaResponse()


def test_sta_proxy_allows_superuser_outside_permission_group(monkeypatch):
    user = SimpleNamespace(permission_group_ids=[], is_superuser=True)
    repo = MagicMock()
    repo.find_one_permission_group_id.return_value = SimpleNamespace(username="test")
    monkeypatch.setattr(sta_proxy.httpx, "AsyncClient", FakeAsyncClient)

    result = asyncio.run(
        sta_proxy.redirect_query(
            permission_group_id=999,
            q="/Things",
            repo=repo,
            current_user=user,
        )
    )

    assert result == {"ok": True}
    repo.find_one_permission_group_id.assert_called_once_with(999)


def test_sta_proxy_keeps_normal_user_permission_check():
    user = SimpleNamespace(permission_group_ids=[1], is_superuser=False)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            sta_proxy.redirect_query(
                permission_group_id=999,
                q="/Things",
                repo=MagicMock(),
                current_user=user,
            )
        )

    assert exc_info.value.status_code == 403


def test_external_trigger_router_passes_superuser_access_scope(monkeypatch):
    user = SimpleNamespace(id=1, permission_group_ids=[], is_superuser=True)
    payload = TriggerSyncExtApiBase(
        ingest_ids=[1], start_date="2026-01-01", end_date="2026-01-02"
    )
    service = MagicMock(return_value={"triggered_ingests": []})
    monkeypatch.setattr(trigger_ext_api, "trigger_external_api_service", service)

    trigger_ext_api.trigger_api(current_user=user, payload=payload, repo=MagicMock())

    access_scope = service.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_quality_control_trigger_router_passes_superuser_access_scope(monkeypatch):
    user = SimpleNamespace(id=1, permission_group_ids=[], is_superuser=True)
    payload = TriggerQualityControl(
        quality_control_setting_ids=[1],
        start_date="2026-01-01",
        end_date="2026-01-02",
    )
    service = MagicMock(return_value={"triggered_quality_control_settings": []})
    monkeypatch.setattr(
        trigger_quality_control, "trigger_quality_control_service", service
    )

    trigger_quality_control.trigger_quality_control(
        payload=payload,
        current_user=user,
        repo_quality_control=MagicMock(),
    )

    access_scope = service.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_external_trigger_service_passes_superuser_scope_to_repository(monkeypatch):
    payload = TriggerSyncExtApiBase(
        ingest_ids=[1], start_date="2026-01-01", end_date="2026-01-02"
    )
    repo = MagicMock()
    repo.find_one.return_value = SimpleNamespace(uuid="ingest-uuid")
    monkeypatch.setattr(
        trigger_ext_api_service_module, "publish_trigger_ext_api", MagicMock()
    )

    result = trigger_ext_api_service_module.trigger_external_api_service(
        payload=payload,
        allowed_permission_group_ids=[],
        repo_ingest=repo,
        access_scope=AccessScope([], is_superuser=True),
    )

    assert result == {"triggered_ingests": [1]}
    access_scope = repo.find_one.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_external_trigger_service_keeps_legacy_permission_groups(monkeypatch):
    payload = TriggerSyncExtApiBase(
        ingest_ids=[1], start_date="2026-01-01", end_date="2026-01-02"
    )
    repo = MagicMock()
    repo.find_one.return_value = SimpleNamespace(uuid="ingest-uuid")
    monkeypatch.setattr(
        trigger_ext_api_service_module, "publish_trigger_ext_api", MagicMock()
    )

    trigger_ext_api_service_module.trigger_external_api_service(payload, [1], repo)

    access_scope = repo.find_one.call_args.kwargs["access_scope"]
    assert access_scope == AccessScope([1])


def test_external_sftp_trigger_router_passes_superuser_access_scope(monkeypatch):
    user = SimpleNamespace(id=1, permission_group_ids=[], is_superuser=True)
    payload = TriggerSyncExtSftpBase(
        ingest_id=1, start_date="2026-01-01", end_date="2026-01-02"
    )
    service = MagicMock(return_value={"triggered_ingest": 1})
    monkeypatch.setattr(trigger_ext_sftp, "trigger_external_sftp_service", service)

    trigger_ext_sftp.trigger_sftp(current_user=user, payload=payload, repo=MagicMock())

    access_scope = service.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_external_sftp_trigger_service_passes_superuser_scope_to_repository(
    monkeypatch,
):
    payload = TriggerSyncExtSftpBase(
        ingest_id=1, start_date="2026-01-01", end_date="2026-01-02"
    )
    repo = MagicMock()
    repo.find_one.return_value = SimpleNamespace(
        ingest=SimpleNamespace(uuid="ingest-uuid")
    )
    monkeypatch.setattr(
        trigger_ext_sftp_service_module, "publish_trigger_ext_sftp", MagicMock()
    )

    result = trigger_ext_sftp_service_module.trigger_external_sftp_service(
        payload=payload,
        repo_ext_sftp=repo,
        access_scope=AccessScope([], is_superuser=True),
    )

    assert result == {"triggered_ingest": 1}
    access_scope = repo.find_one.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_quality_control_trigger_service_passes_superuser_scope(monkeypatch):
    payload = TriggerQualityControl(
        quality_control_setting_ids=[1],
        start_date="2026-01-01",
        end_date="2026-01-02",
    )
    repo = MagicMock()
    repo.find_allowed_one.return_value = SimpleNamespace(
        permission_group=SimpleNamespace(uuid="group-uuid"), name="test"
    )
    monkeypatch.setattr(
        trigger_quality_control_service_module,
        "publish_trigger_quality_control",
        MagicMock(),
    )

    result = trigger_quality_control_service_module.trigger_quality_control_service(
        payload=payload,
        allowed_permission_group_ids=[],
        repo_quality_control=repo,
        access_scope=AccessScope([], is_superuser=True),
    )

    assert result == {"triggered_quality_control_settings": [1]}
    access_scope = repo.find_allowed_one.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


def test_quality_control_trigger_service_keeps_legacy_permission_groups(monkeypatch):
    payload = TriggerQualityControl(
        quality_control_setting_ids=[1],
        start_date="2026-01-01",
        end_date="2026-01-02",
    )
    repo = MagicMock()
    repo.find_allowed_one.return_value = SimpleNamespace(
        permission_group=SimpleNamespace(uuid="group-uuid"), name="test"
    )
    monkeypatch.setattr(
        trigger_quality_control_service_module,
        "publish_trigger_quality_control",
        MagicMock(),
    )

    trigger_quality_control_service_module.trigger_quality_control_service(
        payload, [1], repo
    )

    access_scope = repo.find_allowed_one.call_args.kwargs["access_scope"]
    assert access_scope == AccessScope([1])


def test_ingest_find_one_does_not_filter_superuser_by_permission_group():
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalar_one_or_none.return_value = (
        object()
    )
    repo = IngestRepository(session)

    repo.find_one(1, access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert "permission_group_id IN" not in str(statement)


def test_ingest_find_one_filters_by_permission_group_for_regular_user():
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalar_one_or_none.return_value = (
        object()
    )
    repo = IngestRepository(session)

    repo.find_one(1, access_scope=AccessScope([1]))

    statement = session.exec.call_args.args[0]
    assert "permission_group_id IN" in str(statement)
