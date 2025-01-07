#!/usr/bin/env python3
from __future__ import annotations

import os.path
import pathlib

import psycopg
import requests
import pytest
from environment import *
import docker as docker_sdk
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


@pytest.fixture(scope="session")
def docker() -> docker_sdk.DockerClient:
    return docker_sdk.from_env()


ORCHESTRATION_DIR = pathlib.Path(__file__).parents[1].name
# docker compose constructs names by using the compose file
# directory and the service name and an increasing number,
# unless a service specifies 'container_name'.
DC_CONTAINER = [
    f"{ORCHESTRATION_DIR}-proxy-1",
    f"{ORCHESTRATION_DIR}-frontend-1",
    f"{ORCHESTRATION_DIR}-worker-file-ingest-1",
    f"{ORCHESTRATION_DIR}-worker-object-storage-setup-1",
    f"{ORCHESTRATION_DIR}-worker-mqtt-ingest-1",
    f"{ORCHESTRATION_DIR}-worker-grafana-dashboard-1",
    f"{ORCHESTRATION_DIR}-worker-crontab-setup-1",
    f"{ORCHESTRATION_DIR}-worker-run-qaqc-1",
    f"{ORCHESTRATION_DIR}-worker-frost-setup-1",
    f"{ORCHESTRATION_DIR}-mqtt-cat-1",
    f"{ORCHESTRATION_DIR}-worker-grafana-user-orgs-1",
    f"{ORCHESTRATION_DIR}-object-storage-1",
    f"{ORCHESTRATION_DIR}-worker-configdb-updater-1",
    f"{ORCHESTRATION_DIR}-worker-db-setup-1",
    f"{ORCHESTRATION_DIR}-worker-mqtt-user-creation-1",
    f"{ORCHESTRATION_DIR}-tsmdl-1",
    f"{ORCHESTRATION_DIR}-cron-scheduler-1",
    f"{ORCHESTRATION_DIR}-timeio-db-api-1",
    f"{ORCHESTRATION_DIR}-mqtt-broker-1",
    f"{ORCHESTRATION_DIR}-frost-1",
    f"{ORCHESTRATION_DIR}-visualization-1",
    f"{ORCHESTRATION_DIR}-database-1",
    "cadvisor",  # set by 'container_name' in service monitoring
]


def test_docker_unknown_container(docker):
    unknown = []
    for c in docker.containers.list():
        if c.name not in DC_CONTAINER:
            unknown.append(c.name)
    if unknown:
        raise ValueError(f"Unknown container: {unknown}")


@pytest.mark.parametrize("name", DC_CONTAINER)
def test_docker_services_running(docker, name):
    container = docker.containers.get(name)
    assert container.status == "running"
    # Note that health is unknown if no healthcheck is defined.
    assert container.health in ["healthy", "unknown"]
