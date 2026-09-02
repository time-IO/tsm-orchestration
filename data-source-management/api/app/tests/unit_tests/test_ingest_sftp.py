"""
Tests for the ingest/sftp router (full CRUD).

Differences from the other unit_tests:
- Most sftp-specific fields (username, password, bucket_name,
  fileserver_uri) are generated server-side in create() - the
  Create schema only accepts parser_id and filename_pattern.
- Update schema only allows filename_pattern to be changed.
- create/update additionally depend on get_repo_parser_detailed
  (used to validate payload.parser_id against the user's permission
  groups) - must be mocked too.
- to_flat() builds a nested "parser" dict in addition to the nested
  "permission_group" dict - needs a dummy value in make_ingest_dict
  overrides.
- parser_id is a required (non-Optional) int in IngestSftpRead, so
  it must always be overridden away from make_ingest_dict's None
  default.
"""

import pytest
from fastapi import HTTPException

from dependencies import get_repo_ingest_sftp, get_repo_parser_detailed

ROUTER_MODULE = "routers.ingest_sftp"
BASE_PATH = "/ingest/sftp"


def _sftp_dict(make_ingest_dict, **overrides):
    """Builds a dict for IngestSftpRead: IngestRead fields (via
    make_ingest_dict) + sftp-specific fields."""
    defaults = {
        "parser_id": 1,
        "username": "ingest-sftp-user",
        "password": "secret",
        "bucket_name": "ingest-sftp-bucket",
        "fileserver_uri": "sftp://fileserver.example.com",
        "filename_pattern": "*.csv",
        "parser": {"id": 1, "name": "Default Parser"},
    }
    defaults.update(overrides)
    return make_ingest_dict(**defaults)


def _mock_parser(permission_group_id=1):
    """Builds a stand-in object with just the attribute the router
    actually reads (permission_group_id) - a plain MagicMock would
    work too, but this is more explicit about what's needed."""
    return type("Parser", (), {"permission_group_id": permission_group_id})()


# ---------------------------------------------------------------------------
# read_one
# ---------------------------------------------------------------------------


def test_read_one_found(client, override_repo, make_ingest_dict):
    repo = override_repo(get_repo_ingest_sftp)
    repo.find_one.return_value = object()  # content irrelevant, to_flat is mocked
    repo.to_flat.return_value = _sftp_dict(make_ingest_dict)

    response = client.get(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json()["filename_pattern"] == "*.csv"
    repo.find_one.assert_called_once()


def test_read_one_not_found(client, override_repo):
    repo = override_repo(get_repo_ingest_sftp)
    repo.find_one.side_effect = HTTPException(status_code=404, detail="Not found")

    response = client.get(f"{BASE_PATH}/999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_sftp)
    parser_repo = override_repo(get_repo_parser_detailed)
    repo.create.return_value = (
        object()
    )  # passed to publish_frontend_thing_update + to_flat, content irrelevant
    repo.to_flat.return_value = _sftp_dict(make_ingest_dict)
    parser_repo.find_one.return_value = _mock_parser(permission_group_id=1)
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    payload = {
        "name": "Test SFTP",
        "permission_group_id": 1,
        "parser_id": 1,
        "filename_pattern": "*.csv",
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 200
    repo.create.assert_called_once()
    mock_publish.assert_called_once()


def test_create_with_wrong_permission_group_returns_401(
    client, override_repo, make_ingest_dict
):
    """If the parser belongs to a different permission group than the
    payload, the router rejects with 401 before ever calling repo.create()."""
    repo = override_repo(get_repo_ingest_sftp)
    parser_repo = override_repo(get_repo_parser_detailed)
    parser_repo.find_one.return_value = _mock_parser(permission_group_id=999)

    payload = {
        "name": "Test SFTP",
        "permission_group_id": 1,
        "parser_id": 1,
        "filename_pattern": "*.csv",
    }

    response = client.post(f"{BASE_PATH}/", json=payload)

    assert response.status_code == 401
    repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update(client, override_repo, make_ingest_dict, mock_publish_frontend_update):
    repo = override_repo(get_repo_ingest_sftp)
    repo.update.return_value = object()
    repo.to_flat.return_value = _sftp_dict(make_ingest_dict, filename_pattern="*.json")
    mock_publish = mock_publish_frontend_update(ROUTER_MODULE)

    # Update schema only has filename_pattern (besides the inherited
    # parser_id check) - a single field is enough
    payload = {"filename_pattern": "*.json"}

    response = client.patch(f"{BASE_PATH}/1", json=payload)

    assert response.status_code == 200
    assert response.json()["filename_pattern"] == "*.json"
    repo.update.assert_called_once()
    mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete(client, override_repo):
    repo = override_repo(get_repo_ingest_sftp)
    repo.delete.return_value = {"ok": True}

    response = client.delete(f"{BASE_PATH}/1")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    repo.delete.assert_called_once()
