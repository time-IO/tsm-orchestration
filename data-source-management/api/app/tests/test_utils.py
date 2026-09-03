"""
Shared test utilities.

Import and call setup_test_env() at the very top of every conftest.py,
BEFORE any app imports - settings and the DB engine are built at import
time, so env vars must be set first.

Usage in conftest.py:

    from tests.test_utils import setup_test_env
    setup_test_env()

    from main import app  # noqa: E402 - intentional late import
"""
from __future__ import annotations

import os
from cryptography.fernet import Fernet

import csv
import io
import json

from typing import BinaryIO

from starlette.datastructures import UploadFile




def setup_test_env() -> None:
    """Set required env vars for the test environment.

    Uses setdefault so that real values already set in the environment
    always take precedence. Integration tests that need a real DB
    should set POSTGRES_SERVER etc. BEFORE calling this.
    """
    os.environ.setdefault("POSTGRES_SERVER", "localhost")
    os.environ.setdefault("POSTGRES_USER", "test")
    os.environ.setdefault(
        "OIDC_WELL_KNOWN", "https://example.com/.well-known/openid-configuration"
    )
    os.environ.setdefault("OIDC_ISSUER", "https://example.com")
    os.environ.setdefault("OIDC_AUDIENCE", "test-audience")
    os.environ.setdefault("MINIO_SFTP_PORT", "8022")
    os.environ.setdefault("PROXY_URL", "http://localhost")
    os.environ.setdefault("FERNET_ENCRYPTION_SECRET", Fernet.generate_key().decode())
    os.environ.setdefault("STA_ROOT_URL", "http://localhost/sta")
    os.environ.setdefault("STA_VERSION", "v1.1")
    os.environ.setdefault("MQTT_BROKER_HOST", "localhost")
    os.environ.setdefault("MQTT_CLIENT_ID", "test-client")
    os.environ.setdefault("MQTT_USER", "test")
    os.environ.setdefault("MQTT_PASSWORD", "test")
    os.environ.setdefault("INGEST_MQTT_BROKER_URI", "mqtt://localhost:1883")


class UserProxy:
    """Mimics User without SQLAlchemy session binding.
    Used in tests to avoid session conflicts between the test
    fixture session and FastAPI's internal session."""

    def __init__(self, user, permission_group_ids: list[int]):
        self.id = user.id
        self.sub = user.sub
        self.username = user.username
        self.email = user.email
        self.is_active = user.is_active
        self.is_superuser = user.is_superuser
        self._permission_group_ids = permission_group_ids

    @property
    def permission_group_ids(self) -> list[int]:
        return self._permission_group_ids