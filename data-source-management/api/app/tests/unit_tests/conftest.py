from tests.utils.test_env import setup_test_env

setup_test_env()
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from auth import OIDCError


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
            {
                "name": "gap_window",
                "type": "offset",
                "input": {"value": "2H"},
            },
            {
                "name": "group_window",
                "type": "offset",
                "input": {"value": "1D"},
            },
        ],
    }


@pytest.fixture
def sample_quality_control_function_argument_create():
    from api.app.models.quality_control_setting import (
        QualityControlFunctionArgumentCreate,
    )

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
                name="gap_window", type="offset", input={"value": "2H"}
            ),
            QualityControlFunctionArgumentCreate(
                name="group_window", type="offset", input={"value": "1D"}
            ),
        ],
    )


# ------------------------------------------------------ mock user
from main import app
from dependencies import get_current_user, create_database_if_not_exists
from models import User
import uuid
from datetime import datetime


@pytest.fixture
def mock_user() -> User:
    """Standard test user. Override in individual tests when needed
    (e.g. different permission_group_ids for permission tests)."""
    return User(id=1, permission_group_ids=[1, 2])


@pytest.fixture(autouse=True)
def _reset_dependency_overrides():
    """Clears dependency_overrides after every test - even if the
    test fails. Prevents mocks from 'leaking' between tests."""
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_user) -> TestClient:
    """TestClient with get_current_user already mocked.
    Repo dependencies are mocked additionally per test via
    override_repo."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_no_auth() -> TestClient:
    """TestClient WITHOUT overriding get_current_user - the real
    auth dependency applies. For testing the unauthenticated case."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_oidc_invalid_token(monkeypatch):
    """Patches oidc.authenticate to raise OIDCError -> 401.

    Used to test the invalid/expired token case without a real
    OIDC server. Patch target is dependencies.oidc (the already-
    imported reference in that module), not auth.oidc directly.
    """
    monkeypatch.setattr(
        "dependencies.oidc.authenticate",
        MagicMock(side_effect=OIDCError("Invalid token")),
    )


@pytest.fixture
def mock_publish_frontend_update(monkeypatch):
    """Patches publish_frontend_thing_update in the respective router
    module.

    The path is necessary because `from mqtt import publish_frontend_thing_update`
    creates its own local reference in each router module - patching
    at the source (mqtt.publish_frontend_thing_update) does NOT affect
    references already bound in the router modules.

    Example:

        def test_create(client, mock_publish_frontend_update):
            mock = mock_publish_frontend_update("unit_tests.ingest_external_api_bosch")
            ...
            mock.assert_called_once()
    """

    def _patch(router_module_path: str) -> MagicMock:
        mock = MagicMock()
        monkeypatch.setattr(f"{router_module_path}.publish_frontend_thing_update", mock)
        return mock

    return _patch


@pytest.fixture
def override_repo():
    """Fixture factory for mocking any repo dependency.

    Example:

        def test_list(client, override_repo):
            repo = override_repo(get_repo_ingest_external_api)
            repo.find_all.return_value = []

            response = client.get("/ingest/external-api/")
            ...
    """

    def _override(dependency, **mock_kwargs) -> MagicMock:
        mock = MagicMock(**mock_kwargs)
        app.dependency_overrides[dependency] = lambda: mock
        return mock

    return _override


@pytest.fixture
def make_ingest_dict():
    """Fixture factory: builds a dict with the required fields from
    IngestRead. Useful for tests of all unit_tests whose response_model
    is based on IngestRead (IngestExternalApiRead, IngestSftpRead, ...).
    Override/extend individual fields via keyword args - e.g. the
    subclass-specific fields like api_type, sync_enabled.

    "permission_group" is only typed as a `dict` -> the default is
    enough for validation, content doesn't matter otherwise.

    Example:

        def test_x(make_ingest_dict):
            data = make_ingest_dict(
                name="Test API", api_type="dwd", sync_enabled=True,
                sync_interval_in_minutes=15,
            )
    """

    def _make(**overrides) -> dict:
        base = {
            "id": 1,
            "uuid": uuid.uuid4(),
            "created_at": datetime.now(),
            "ingest_type": "external_api",
            "name": "Test",
            "permission_group_id": 1,
            "description": None,
            "created_by_id": None,
            "parser_id": None,
            "permission_group": {"id": 1, "name": "Default"},
        }
        base.update(overrides)
        return base

    return _make


@pytest.fixture(autouse=True)
def mock_db_dependency():
    """Neutralizes create_database_if_not_exists globally for all
    tests, so create/update endpoints don't try to hit a real
    database during request handling."""
    app.dependency_overrides[create_database_if_not_exists] = lambda: None
    yield
    app.dependency_overrides.pop(create_database_if_not_exists, None)
