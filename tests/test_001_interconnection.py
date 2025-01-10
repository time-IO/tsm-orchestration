#!/usr/bin/env python3
from __future__ import annotations

import warnings
import pytest
from docker import DockerClient
from docker.models.containers import ExecResult, Container


@pytest.fixture(scope="session")
def docker() -> DockerClient:
    cl = DockerClient.from_env()
    yield cl
    cl.close()


@pytest.fixture(scope="module")
def container(request, docker: DockerClient) -> Container:
    return docker.containers.get(request.param)


dbapi_test_script = """
import requests, os
url = os.environ["DB_API_BASE_URL"]
resp = requests.get(f"{url}/health")
resp.raise_for_status()
print("someUniqueStringToCheckAgainst")
"""


db_test = """
import psycopg, os
url = os.environ["DATABASE_URL"]
with psycopg.connect(url) as conn:  
    one = conn.execute("select 1").fetchone()
    assert one is not None and one[0] == 1
print("someUniqueStringToCheckAgainst")
"""


def run_in_container(container, script) -> ExecResult:
    """Runs a script in a running docker container"""
    assert script[0] == "\n"
    assert script[-1] == "\n"
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="^This is a rather awkward situation.*urllib3.*",
            category=DeprecationWarning,
        )
        return container.exec_run(f"bash -c 'python3 - <<EOF{script}EOF'")


@pytest.mark.parametrize(
    "container", ["tsm-orchestration-worker-db-setup-1"], indirect=True
)
@pytest.mark.parametrize(
    "script",
    [
        pytest.param(dbapi_test_script, id="DB_API_BASE_URL-Connection"),
        pytest.param(db_test, id="DATABASE_URL-Connection"),
        # pytest.param(..., id="MQTT_BROKER-Connection"),
    ],
)
def test__worker_db_setup(container, script):
    result = run_in_container(container, script)
    assert result.exit_code == 0
    assert b"someUniqueStringToCheckAgainst" in result.output


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
        "tsm-orchestration-worker-mqtt-user-creation-1",
        "tsm-orchestration-cron-scheduler-1",
    ],
    indirect=True,  # passing params to fixture
)
def test_connections(container, script):
    """Test connection to other service from within a container"""
    result = run_in_container(container, script)
    assert result.exit_code == 0
    assert b"someUniqueStringToCheckAgainst" in result.output
