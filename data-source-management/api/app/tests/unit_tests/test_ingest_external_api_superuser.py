from unittest.mock import MagicMock

import pytest

from access_scope import AccessScope
from dependencies import (
    get_repo_ingest_external_api,
    get_repo_ingest_external_api_dwd,
    get_repo_ingest_external_api_neutron_monitor,
    get_repo_ingest_external_api_sensoto,
    get_repo_ingest_external_api_the_things_network,
    get_repo_ingest_external_api_tsystems,
    get_repo_ingest_external_api_uba,
)
from repositories.ingest_external_api_dwd import IngestExternalApiDwdRepository
from repositories.ingest_external_api_neutron_monitor import (
    IngestExternalApiNeutronMonitorRepository,
)
from repositories.ingest_external_api_sensoto import (
    IngestExternalApiSensotoRepository,
)
from repositories.ingest_external_api_the_things_network import (
    IngestExternalApiTheThingsNetworkRepository,
)
from repositories.ingest_external_api_tsystems import (
    IngestExternalApiTSystemsRepository,
)
from repositories.ingest_external_api_uba import IngestExternalApiUbaRepository
from routers import (
    ingest_external_api_dwd,
    ingest_external_api_neutron_monitor,
    ingest_external_api_sensoto,
    ingest_external_api_the_things_network,
    ingest_external_api_tsystems,
    ingest_external_api_uba,
)

LIST_CASES = (
    ("/ingest/external-api/", get_repo_ingest_external_api),
    ("/ingest/external-api/dwd/", get_repo_ingest_external_api_dwd),
    (
        "/ingest/external-api/neutron-monitor/",
        get_repo_ingest_external_api_neutron_monitor,
    ),
    ("/ingest/external-api/sensoto/", get_repo_ingest_external_api_sensoto),
    (
        "/ingest/external-api/the-things-network/",
        get_repo_ingest_external_api_the_things_network,
    ),
    ("/ingest/external-api/tsystems/", get_repo_ingest_external_api_tsystems),
    ("/ingest/external-api/uba/", get_repo_ingest_external_api_uba),
)

PROVIDER_CASES = (
    (ingest_external_api_dwd, IngestExternalApiDwdRepository),
    (
        ingest_external_api_neutron_monitor,
        IngestExternalApiNeutronMonitorRepository,
    ),
    (ingest_external_api_sensoto, IngestExternalApiSensotoRepository),
    (
        ingest_external_api_the_things_network,
        IngestExternalApiTheThingsNetworkRepository,
    ),
    (ingest_external_api_tsystems, IngestExternalApiTSystemsRepository),
    (ingest_external_api_uba, IngestExternalApiUbaRepository),
)


@pytest.mark.parametrize(("path", "dependency"), LIST_CASES)
def test_read_list_passes_superuser_access_scope(
    path, dependency, client, mock_user, override_repo
):
    mock_user.is_superuser = True
    repo = override_repo(dependency)
    repo.find_all.return_value = []

    response = client.get(path)

    assert response.status_code == 200
    access_scope = repo.find_all.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


@pytest.mark.parametrize(("router_module", "repository_class"), PROVIDER_CASES)
def test_read_one_passes_superuser_access_scope(
    router_module, repository_class, mock_user
):
    mock_user.is_superuser = True
    repo = MagicMock(spec=repository_class)
    repo.find_one.return_value = object()

    router_module.read_one(id=1, current_user=mock_user, repo=repo)

    access_scope = repo.find_one.call_args.kwargs["access_scope"]
    assert access_scope.is_superuser is True


@pytest.mark.parametrize(("router_module", "repository_class"), PROVIDER_CASES)
def test_find_all_does_not_filter_superuser_by_permission_group(
    router_module, repository_class
):
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalars.return_value.all.return_value = (
        []
    )
    repo = repository_class(session)

    repo.find_all(access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert statement.whereclause is None


@pytest.mark.parametrize(("router_module", "repository_class"), PROVIDER_CASES)
def test_find_one_does_not_filter_superuser_by_permission_group(
    router_module, repository_class
):
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalar_one_or_none.return_value = (
        object()
    )
    repo = repository_class(session)

    repo.find_one(1, access_scope=AccessScope([], is_superuser=True))

    statement = session.exec.call_args.args[0]
    assert "permission_group_id IN" not in str(statement)


@pytest.mark.parametrize(("router_module", "repository_class"), PROVIDER_CASES)
def test_find_all_keeps_positional_permission_group_filter(
    router_module, repository_class
):
    session = MagicMock()
    session.exec.return_value.unique.return_value.scalars.return_value.all.return_value = (
        []
    )
    repo = repository_class(session)

    repo.find_all([1])

    statement = session.exec.call_args.args[0]
    assert statement.whereclause is not None
