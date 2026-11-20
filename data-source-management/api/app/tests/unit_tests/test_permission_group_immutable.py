import importlib
import pkgutil
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import models
from models.ingest import IngestUpdate
from models.ingest_external_sftp import IngestExternalSftpUpdate
from models.ingest_http import IngestHttpUpdate
from models.ingest_sftp import IngestSftpUpdate
from models.quality_control_setting import QualityControlSettingUpdate
from repositories.parser_detailed import ParserDetailedRepository
from routers import ingest_external_sftp, ingest_http, ingest_sftp

for _module in pkgutil.iter_modules(models.__path__):
    importlib.import_module(f"models.{_module.name}")


def _subclasses(cls):
    for sub in cls.__subclasses__():
        yield sub
        yield from _subclasses(sub)


UPDATE_MODELS = (
    IngestUpdate,
    *_subclasses(IngestUpdate),
    QualityControlSettingUpdate,
)
ROUTER_CASES = (
    (ingest_http, IngestHttpUpdate),
    (ingest_sftp, IngestSftpUpdate),
    (ingest_external_sftp, IngestExternalSftpUpdate),
)


@pytest.mark.parametrize("model", UPDATE_MODELS, ids=lambda m: m.__name__)
def test_update_model_drops_permission_group_id(model):
    payload = model.model_validate({"permission_group_id": 2})

    assert "permission_group_id" not in payload.model_dump(exclude_unset=True)


def _call_update(router_module, payload_cls, payload, mock_user, monkeypatch):
    monkeypatch.setattr(router_module, "publish_frontend_thing_update", MagicMock())
    repo = MagicMock()
    repo.find_one.return_value = SimpleNamespace(
        ingest=SimpleNamespace(permission_group_id=1)
    )
    parser_repo = MagicMock(spec=ParserDetailedRepository)
    parser_repo.find_one.return_value = SimpleNamespace(
        permission_group_id=payload.pop("parser_group", 1)
    )
    router_module.update(
        id=7,
        payload=payload_cls.model_validate(payload),
        current_user=mock_user,
        repo=repo,
        parser_repo=parser_repo,
    )
    return repo, parser_repo


@pytest.mark.parametrize(("router_module", "payload_cls"), ROUTER_CASES)
def test_update_rejects_parser_from_other_group(
    router_module, payload_cls, mock_user, monkeypatch
):
    # payload group matches the parser, but the stored ingest group wins
    payload = {"parser_id": 3, "parser_group": 2, "permission_group_id": 2}

    with pytest.raises(HTTPException) as exc_info:
        _call_update(router_module, payload_cls, payload, mock_user, monkeypatch)

    assert exc_info.value.status_code == 401


@pytest.mark.parametrize(("router_module", "payload_cls"), ROUTER_CASES)
def test_update_accepts_parser_from_ingest_group(
    router_module, payload_cls, mock_user, monkeypatch
):
    repo, _ = _call_update(
        router_module, payload_cls, {"parser_id": 3}, mock_user, monkeypatch
    )

    assert repo.find_one.call_args.args == (7,)
    repo.update.assert_called_once()


@pytest.mark.parametrize(("router_module", "payload_cls"), ROUTER_CASES)
def test_update_without_parser_skips_parser_check(
    router_module, payload_cls, mock_user, monkeypatch
):
    repo, parser_repo = _call_update(
        router_module, payload_cls, {"name": "renamed"}, mock_user, monkeypatch
    )

    repo.find_one.assert_not_called()
    parser_repo.find_one.assert_not_called()
    repo.update.assert_called_once()
