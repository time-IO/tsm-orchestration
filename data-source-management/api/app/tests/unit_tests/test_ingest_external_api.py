"""
Tests for the ingest/external-api router.

Uses the shared fixtures from tests/conftest.py (client,
override_repo, mock_user). Repo logic itself is not tested here,
only the API layer: status codes, pagination format, correct
forwarding of query parameters to find_all().
"""

from dependencies import get_repo_ingest_external_api


def test_read_list_empty(client, override_repo):
    repo = override_repo(get_repo_ingest_external_api)
    repo.find_all.return_value = []

    response = client.get("/ingest/external-api/")

    assert response.status_code == 200
    assert response.json()["items"] == []
    repo.find_all.assert_called_once()


def test_read_list_with_items(client, override_repo, make_ingest_dict):
    repo = override_repo(get_repo_ingest_external_api)
    repo.find_all.return_value = [
        make_ingest_dict(
            name="Test API",
            api_type="dwd",
            sync_enabled=True,
            sync_interval_in_minutes=15,
        )
    ]

    response = client.get("/ingest/external-api/")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_read_list_passes_sort_by(client, override_repo):
    repo = override_repo(get_repo_ingest_external_api)
    repo.find_all.return_value = []

    client.get("/ingest/external-api/?sort_by=name:asc")

    assert repo.find_all.call_args.kwargs["sort_by"] == "name:asc"


def test_read_list_passes_access_scope(client, override_repo, mock_user):
    repo = override_repo(get_repo_ingest_external_api)
    repo.find_all.return_value = []

    client.get("/ingest/external-api/")

    access_scope = repo.find_all.call_args.kwargs["access_scope"]
    assert access_scope.permission_group_ids == mock_user.permission_group_ids


def test_read_list_unauthenticated(client_no_auth):
    response = client_no_auth.get("/ingest/external-api/")
    assert response.status_code in (401, 403)
