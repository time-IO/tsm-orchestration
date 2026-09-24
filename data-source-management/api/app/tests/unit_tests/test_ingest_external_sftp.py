"""
Tests for the ingest/external-sftp router (full CRUD).

Differences from the other external-* unit_tests:
- create/update additionally depend on get_repo_parser_detailed
  (used to validate payload.parser_id against the user's permission
  groups). Must be mocked too, otherwise it falls through to a real
  repo/DB call.
- to_flat() builds a nested "parser" dict (parser.parser_info) in
  addition to the nested "permission_group" dict - both need dummy
  values in make_ingest_dict overrides.
- IngestExternalSftpCreate requires parser_id, uri, path, and
  filename_pattern as mandatory fields.
"""

import pytest
from fastapi import HTTPException

from dependencies import get_repo_ingest_external_sftp, get_repo_parser_detailed

ROUTER_MODULE = "routers.ingest_external_sftp"
BASE_PATH = "/ingest/external-sftp"


def _sftp_dict(make_ingest_dict, **overrides):
    """Builds a dict for IngestExternalSftpRead: IngestRead fields
    (via make_ingest_dict) + sftp-specific fields. parser_id is part
    of IngestRead already (via make_ingest_dict's base dict), so it's
    not repeated here unless overridden."""
    defaults = {
        "parser_id": 1,
        "uri": "sftp://example.com",
        "path": "/data",
        "username": "sftpuser",
        "password": "secret",
        "bucket_username": "bucket-user",
        "bucket_password": "bucket-secret",
        "sync_interval_in_minutes": 15,
        "sync_enabled": True,
        "filename_pattern": "*.csv",
        "ssh_public_key": "ssh-rsa AAAA...",
        "parser": {"id": 1, "name": "Default Parser"},
    }
    defaults.update(overrides)
    return make_ingest_dict(**defaults)


# ---------------------------------------------------------------------------
# read_one
# ---------------------------------------------------------------------------


def test_read_one_found(client, override_repo, make_ingest_dict):
    repo = override_repo(get_repo_ingest_external_sftp)
    repo.find_one.return_value = object()  # content irrelevant, to_flat is mocked
    repo.to_flat.return_value = _sftp_dict(make_ingest_dict)

    response = client.get(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json()["uri"] == "sftp://example.com"
    repo.find_one.assert_called_once()


def test_read_one_not_found(client, override_repo):
    repo = override_repo(get_repo_ingest_external_sftp)
    repo.find_one.side_effect = HTTPException(status_code=404, detail="Not found")

    response = client.get(f"{BASE_PATH}/999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_external_sftp)
    parser_repo = override_repo(get_repo_parser_detailed)
    repo.create.return_value = object()
    repo.to_flat.return_value = _sftp_dict(make_ingest_dict)
    parser_repo.find_one.return_value = type("Parser", (), {"permission_group_id": 1})()
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    # parser_id included; parser_repo.find_one is mocked above
    payload = {
        "name": "Test SFTP",
        "permission_group_id": 1,
        "uri": "sftp://example.com",
        "path": "/data",
        "filename_pattern": "*.csv",
        "parser_id": 1,
        "sync_enabled": True,
        "sync_interval_in_minutes": 15,
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 200
    repo.create.assert_called_once()
    mock_publish.assert_called_once()


def test_create_with_parser_id_checks_permission(
    client, override_repo, make_ingest_dict, mock_publish_frontend_update
):
    """When parser_id is set, the router validates it against
    parser_repo before calling repo.create()."""
    repo = override_repo(get_repo_ingest_external_sftp)
    parser_repo = override_repo(get_repo_parser_detailed)
    repo.create.return_value = object()
    repo.to_flat.return_value = _sftp_dict(make_ingest_dict)
    parser_repo.find_one.return_value = type("Parser", (), {"permission_group_id": 1})()
    mock_publish_frontend_update(ROUTER_MODULE)

    payload = {
        "name": "Test SFTP",
        "permission_group_id": 1,
        "uri": "sftp://example.com",
        "path": "/data",
        "filename_pattern": "*.csv",
        "parser_id": 1,
        "sync_enabled": True,
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 200
    parser_repo.find_one.assert_called_once()
    repo.create.assert_called_once()


def test_create_with_parser_id_wrong_permission_group_returns_401(
    client, override_repo, make_ingest_dict
):
    """If the parser belongs to a different permission group than the
    payload, the router rejects with 401 before ever calling repo.create()."""
    repo = override_repo(get_repo_ingest_external_sftp)
    parser_repo = override_repo(get_repo_parser_detailed)
    parser_repo.find_one.return_value = type(
        "Parser", (), {"permission_group_id": 999}
    )()

    payload = {
        "name": "Test SFTP",
        "permission_group_id": 1,
        "uri": "sftp://example.com",
        "path": "/data",
        "filename_pattern": "*.csv",
        "parser_id": 1,
        "sync_enabled": True,
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 401
    repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_external_sftp)
    repo.update.return_value = object()
    repo.to_flat.return_value = _sftp_dict(make_ingest_dict, path="/new-data")
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    # Update schema: all fields optional (PATCH semantics) -> a single
    # field is enough, the rest stays unchanged
    payload = {"path": "/new-data"}

    response = client.patch(f"{BASE_PATH}/1", json=payload)

    assert response.status_code == 200
    assert response.json()["path"] == "/new-data"
    repo.update.assert_called_once()
    mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete(client, override_repo):
    repo = override_repo(get_repo_ingest_external_sftp)
    repo.delete.return_value = {"ok": True}

    response = client.delete(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    repo.delete.assert_called_once()
