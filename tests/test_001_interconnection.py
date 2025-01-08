#!/usr/bin/env python3
from __future__ import annotations
import requests
import pytest
from environment import *
import docker as docker_sdk


@pytest.fixture(scope="module")
def docker() -> docker_sdk.DockerClient:
    cl = docker_sdk.from_env()
    yield cl
    cl.close()


@pytest.fixture(scope="module")
def container(request, docker: docker_sdk.DockerClient):
    return docker.containers.get(request.param)


dbapi_test_script = """
import requests, os
url = os.environ["DB_API_BASE_URL"]
resp = requests.get(f"{url}/health")
resp.raise_for_status()
print("someUniqueStringToCheckAgainst")
"""


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.parametrize("script", [pytest.param(dbapi_test_script, id="DBAPI-script")])
@pytest.mark.parametrize(
    "container",
    [
        "tsm-orchestration-worker-file-ingest-1",
        "tsm-orchestration-worker-object-storage-setup-1",
        "tsm-orchestration-worker-mqtt-ingest-1",
        "tsm-orchestration-worker-grafana-dashboard-1",
        "tsm-orchestration-worker-crontab-setup-1",
        "tsm-orchestration-worker-run-qaqc-1",
        "tsm-orchestration-worker-frost-setup-1",
        "tsm-orchestration-worker-grafana-user-orgs-1",
        "tsm-orchestration-worker-db-setup-1",
        "tsm-orchestration-worker-mqtt-user-creation-1",
        "tsm-orchestration-cron-scheduler-1",
    ],
    indirect=True,  # passing params to fixture
)
def test_connections(container, script):
    """Test connection to other service from within a container"""
    assert script[0] == "\n"
    assert script[-1] == "\n"
    result = container.exec_run(f"bash -c 'python3 - <<EOF{script}EOF'")
    assert result.exit_code == 0
    # find the string the script prints
    assert b"someUniqueStringToCheckAgainst" in result.output
