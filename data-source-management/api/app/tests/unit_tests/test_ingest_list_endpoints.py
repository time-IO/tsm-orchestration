"""
Generic pattern for "all list endpoints".

Your list unit_tests are structurally identical (Page[...] response,
current_user + repo as dependency, sort_by query param). Instead of
copying the happy-path test for every router, this is parametrized
via a registry. Just extend LIST_ENDPOINTS whenever a new router
with its own read_list endpoint is added.

Note: unit_tests like ingest_external_api_bosch, ..._dwd, ..._neutron_monitor
etc. don't have their own read_list endpoint - they're listed via the
shared /ingest/external-api/ endpoint (filtered by api_type) - so they
don't belong in this registry.
"""

import pytest

from dependencies import (
    get_repo_ingest_external_api,
    get_repo_ingest_mqtt,
    get_repo_ingest_sftp,
    get_repo_ingest_external_sftp,
)

LIST_ENDPOINTS = [
    {"prefix": "/ingest/external-api/", "repo_dep": get_repo_ingest_external_api},
    {"prefix": "/ingest/mqtt/", "repo_dep": get_repo_ingest_mqtt},
    {"prefix": "/ingest/sftp/", "repo_dep": get_repo_ingest_sftp},
    {"prefix": "/ingest/external-sftp/", "repo_dep": get_repo_ingest_external_sftp},
    # add further unit_tests with their own read_list endpoint here ...
]


@pytest.mark.parametrize("endpoint", LIST_ENDPOINTS, ids=lambda e: e["prefix"])
def test_read_list_generic_returns_200(client, override_repo, endpoint):
    repo = override_repo(endpoint["repo_dep"])
    repo.find_all.return_value = []

    response = client.get(endpoint["prefix"])

    assert response.status_code == 200
    assert response.json()["items"] == []
