#!/usr/bin/env python3
from __future__ import annotations
import psycopg
import requests
import pytest
from environment import *
import python_on_whales
import warnings


@pytest.mark.parametrize(
    "dsn",
    [
        OBS_DB_DSN,
        CONF_DB_DSN,
        FE_DB_DSN,
        pytest.param(
            CV_DB_DSN,
            marks=pytest.mark.skipif(
                CV_ACCESS_TYPE != "db",
                reason=(
                    f"CV-Database is not tested, because "
                    f"$CV_ACCESS_TYPE is not set to 'db'"
                ),
            ),
        ),
        pytest.param(
            SMS_DB_DSN,
            marks=pytest.mark.skipif(
                SMS_ACCESS_TYPE != "db",
                reason=(
                    f"SMS-Database is not tested, because "
                    f"$SMS_ACCESS_TYPE is not set to 'db'"
                ),
            ),
        ),
    ],
)
def test_database_online(dsn):
    conn: psycopg.Connection
    with psycopg.connect(dsn) as conn:
        one = conn.execute("select 1").fetchone()
        assert one is not None and one[0] == 1


@pytest.mark.skipif(
    SMS_ACCESS_TYPE != "api",
    reason=f"SMS API is not tested, because $SMS_ACCESS_TYPE is not set to 'api'",
)
def test_sms_api_online():
    resp = requests.head(SMS_API_URL, timeout=1)
    resp.raise_for_status()


@pytest.mark.skipif(
    CV_ACCESS_TYPE != "api",
    reason=f"CV API is not tested, because $CV_ACCESS_TYPE is not set to 'api'",
)
def test_cv_api_online():
    resp = requests.head(CV_API_URL, timeout=1)
    resp.raise_for_status()


DC_PROJECT = "tsm-orchestration"


@pytest.fixture(scope="session")
def docker() -> python_on_whales.DockerClient:
    for proj in python_on_whales.docker.compose.ls():
        if proj.name == DC_PROJECT:
            break
    else:
        pytest.exit(
            f"No running docker compose project with name {DC_PROJECT!r} found. "
            f"Stopping further pytesting",
            returncode=2,
        )
    return python_on_whales.DockerClient(compose_files=proj.config_files)


DC_CONTAINER = [
    "tsm-orchestration-proxy-1",
    "tsm-orchestration-frontend-1",
    "tsm-orchestration-worker-file-ingest-1",
    "tsm-orchestration-worker-object-storage-setup-1",
    "tsm-orchestration-worker-mqtt-ingest-1",
    "tsm-orchestration-worker-grafana-dashboard-1",
    "tsm-orchestration-worker-crontab-setup-1",
    "tsm-orchestration-worker-run-qaqc-1",
    "tsm-orchestration-worker-frost-setup-1",
    "tsm-orchestration-mqtt-cat-1",
    "tsm-orchestration-worker-grafana-user-orgs-1",
    "tsm-orchestration-object-storage-1",
    "tsm-orchestration-worker-configdb-updater-1",
    "tsm-orchestration-worker-db-setup-1",
    "tsm-orchestration-worker-mqtt-user-creation-1",
    "tsm-orchestration-tsmdl-1",
    "tsm-orchestration-cron-scheduler-1",
    "tsm-orchestration-timeio-db-api-1",
    "tsm-orchestration-mqtt-broker-1",
    "tsm-orchestration-frost-1",
    "tsm-orchestration-visualization-1",
    "tsm-orchestration-database-1",
    "cadvisor"
]


def test_docker_unknown_container(docker):
    containers = docker.container.list()
    unknown = []
    for c in containers:
        if c.name not in DC_CONTAINER:
            unknown.append(c.name)
    if unknown:
        raise ValueError(f"Unknown container: {unknown}")


@pytest.mark.parametrize("name", DC_CONTAINER)
def test_docker_services_running(docker, name):
    container = docker.container.inspect(name)
    assert container.state.status == "running"
    if container.state.health is not None:
        assert container.state.health.status == "healthy"
