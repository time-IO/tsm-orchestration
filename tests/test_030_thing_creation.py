import json
import os
import time
import uuid
import warnings
from dataclasses import dataclass

import pytest
from docker import DockerClient
from docker.models.containers import ExecResult, Container
import psycopg
from environment import FE_DB_DSN, LOCAL


@pytest.fixture(scope="session")
def docker() -> DockerClient:
    cl = DockerClient.from_env()
    yield cl
    cl.close()


@pytest.fixture(scope="module")
def container(request, docker: DockerClient) -> Container:
    return docker.containers.get(request.param)


@pytest.fixture(scope="module")
def frontend(docker) -> Container:
    return docker.containers.get("tsm-orchestration-frontend-1")


thing_json_template = """
[
  {
    "model": "tsm.thing",
    "fields": {
      "name": "DemoThing99",
      "thing_id": "0a308373-ab29-4317-b351-1443e8a1babd",
      "datasource_type": "SFTP",
      "group": 1,
      "description": "fooo foo fo",
      "sftp_filename_pattern": "*.csv",
      "mqtt_uri": null,
      "mqtt_username": null,
      "mqtt_password": null,
      "mqtt_hashed_password": null,
      "mqtt_topic": null,
      "mqtt_device_type": null,
      "qaqc_ctx_window": "3",
      "qaqc_tests": null,
      "parser": [1]
    }
  }
]
"""


@dataclass
class Thing:
    name: str
    thing_id: int
    datasource_type: str
    group: str
    description: str
    sftp_filename_pattern: str
    mqtt_uri: str
    mqtt_username: str
    mqtt_password: str
    mqtt_hashed_password: str
    mqtt_topic: str
    mqtt_device_type: str
    qaqc_ctx_window: int
    qaqc_tests: list
    parser: str


@pytest.fixture()
def thing_json():
    return thing_json_template


# Equivalent command on CL:
# $ docker compose exec -T frontend python3 manage.py loaddata --format json - < FILE
def test_create_thing(frontend, thing_json):
    """
    Send a MQTT message on the topic `frontend_thing_update`.
    """
    content = json.dumps(json.loads(thing_json))
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="^This is a rather awkward situation.*urllib3.*",
            category=DeprecationWarning,
        )
        cmd = f'python3 manage.py loaddata --format json - <<"EOF"\n{content}\nEOF'
        result = frontend.exec_run(f"bash -c '{cmd}'")
        assert result.exit_code == 0
        assert b"Installed 1 object(s) from 1 fixture(s)" in result.output
