import functools
from types import SimpleNamespace

import httpx
import pytest

from config import settings
from dependencies import get_repo_ingest
from utils.db_api import FakeDbApi

INGEST_UUID = "11111111-1111-1111-1111-111111111111"
DB_API_BASE_URL = "http://db-api:8001"
DB_API_TOKEN = "test-token"


@pytest.fixture
def sample_datastream_refs():
    return ["ds1", "ds2", "ds3"]


@pytest.fixture
def sample_qc_function_payload():
    return {
        "name": "flagIsolated",
        "quality_control_function_arguments": [
            {
                "name": "field",
                "type": "datastream",
                "input": {"value": ["temperature_sensor_1"]},
            },
            {"name": "gap_window", "type": "offset", "input": {"value": "2H"}},
            {"name": "group_window", "type": "offset", "input": {"value": "1D"}},
        ],
    }


@pytest.fixture
def sample_quality_control_function_argument_create():
    from models.quality_control_setting import QualityControlFunctionArgumentCreate

    return QualityControlFunctionArgumentCreate(
        name="field", type="datastream", input={"value": ["ds1"]}
    )


@pytest.fixture
def sample_quality_control_function_create():
    from models.quality_control_setting import (
        QualityControlFunctionArgumentCreate,
        QualityControlFunctionCreate,
    )

    return QualityControlFunctionCreate(
        name="flagIsolated",
        quality_control_function_arguments=[
            QualityControlFunctionArgumentCreate(
                name="field", type="datastream", input={"value": ["ds1"]}
            ),
            QualityControlFunctionArgumentCreate(
                name="gap_window", type="offset", input={"value": "2h"}
            ),
            QualityControlFunctionArgumentCreate(
                name="group_window", type="offset", input={"value": "1D"}
            ),
        ],
    )


@pytest.fixture
def db_api(monkeypatch) -> FakeDbApi:
    """Configured db-api settings + every AsyncClient served by FakeDbApi."""
    monkeypatch.setattr(settings, "DB_API_BASE_URL", DB_API_BASE_URL)
    monkeypatch.setattr(settings, "DB_API_AUTH_TOKEN", DB_API_TOKEN)

    fake = FakeDbApi(DB_API_BASE_URL)
    monkeypatch.setattr(
        "httpx.AsyncClient",
        functools.partial(
            httpx.AsyncClient, transport=httpx.MockTransport(fake.handle)
        ),
    )
    return fake


@pytest.fixture
def db_api_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "DB_API_BASE_URL", "")


@pytest.fixture
def mock_ingest(override_repo):
    """Make repo.find_one return a stub ingest; returns the repo mock."""

    def _mock(uuid: str = INGEST_UUID, **attrs):
        repo = override_repo(get_repo_ingest)
        repo.find_one.return_value = SimpleNamespace(uuid=uuid, **attrs)
        return repo

    return _mock