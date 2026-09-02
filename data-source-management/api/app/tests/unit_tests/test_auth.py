"""
Auth/permission unit tests.

Tests the router layer for auth errors (401/403).
No real OIDC server needed - oidc.authenticate is mocked.

Scenarios:
- No token (missing Authorization header)     -> 401
- Invalid/expired token (OIDCError)           -> 401
- Inactive user (403)                         -> integration test (requires real DB user)
"""

import pytest

PROTECTED_ENDPOINTS = [
    # ingest/external-api
    ("GET", "/ingest/external-api/"),
    # ingest/external-api/bosch
    ("GET", "/ingest/external-api/bosch/"),
    ("GET", "/ingest/external-api/bosch/1"),
    ("POST", "/ingest/external-api/bosch/"),
    ("PATCH", "/ingest/external-api/bosch/1"),
    ("DELETE", "/ingest/external-api/bosch/1"),
    # ingest/external-api/dwd
    ("GET", "/ingest/external-api/dwd/"),
    ("GET", "/ingest/external-api/dwd/1"),
    ("POST", "/ingest/external-api/dwd/"),
    ("PATCH", "/ingest/external-api/dwd/1"),
    ("DELETE", "/ingest/external-api/dwd/1"),
    # ingest/external-api/neutron-monitor
    ("GET", "/ingest/external-api/neutron-monitor/"),
    ("GET", "/ingest/external-api/neutron-monitor/1"),
    ("POST", "/ingest/external-api/neutron-monitor/"),
    ("PATCH", "/ingest/external-api/neutron-monitor/1"),
    ("DELETE", "/ingest/external-api/neutron-monitor/1"),
    # ingest/external-api/sensoto
    ("GET", "/ingest/external-api/sensoto/"),
    ("GET", "/ingest/external-api/sensoto/1"),
    ("POST", "/ingest/external-api/sensoto/"),
    ("PATCH", "/ingest/external-api/sensoto/1"),
    ("DELETE", "/ingest/external-api/sensoto/1"),
    # ingest/external-api/the-things-network
    ("GET", "/ingest/external-api/the-things-network/"),
    ("GET", "/ingest/external-api/the-things-network/1"),
    ("POST", "/ingest/external-api/the-things-network/"),
    ("PATCH", "/ingest/external-api/the-things-network/1"),
    ("DELETE", "/ingest/external-api/the-things-network/1"),
    # ingest/external-api/tsystems
    ("GET", "/ingest/external-api/tsystems/"),
    ("GET", "/ingest/external-api/tsystems/1"),
    ("POST", "/ingest/external-api/tsystems/"),
    ("PATCH", "/ingest/external-api/tsystems/1"),
    ("DELETE", "/ingest/external-api/tsystems/1"),
    # ingest/external-api/uba
    ("GET", "/ingest/external-api/uba/"),
    ("GET", "/ingest/external-api/uba/1"),
    ("POST", "/ingest/external-api/uba/"),
    ("PATCH", "/ingest/external-api/uba/1"),
    ("DELETE", "/ingest/external-api/uba/1"),
    # ingest/external-sftp
    ("GET", "/ingest/external-sftp/"),
    ("GET", "/ingest/external-sftp/1"),
    ("POST", "/ingest/external-sftp/"),
    ("PATCH", "/ingest/external-sftp/1"),
    ("DELETE", "/ingest/external-sftp/1"),
    # ingest/mqtt
    ("GET", "/ingest/mqtt/"),
    ("GET", "/ingest/mqtt/1"),
    ("POST", "/ingest/mqtt/"),
    ("PATCH", "/ingest/mqtt/1"),
    ("DELETE", "/ingest/mqtt/1"),
    # ingest
    ("GET", "/ingest/"),
    ("DELETE", "/ingest/1"),
    # ingest/sftp
    ("GET", "/ingest/sftp/"),
    ("GET", "/ingest/sftp/1"),
    ("POST", "/ingest/sftp/"),
    ("PATCH", "/ingest/sftp/1"),
    ("DELETE", "/ingest/sftp/1"),
    # neutron-monitor-station
    ("GET", "/neutron-monitor-station/"),
    ("GET", "/neutron-monitor-station/1"),
    # parser/csv
    ("GET", "/parser/csv/"),
    ("GET", "/parser/csv/1"),
    ("POST", "/parser/csv/"),
    ("PATCH", "/parser/csv/1"),
    ("DELETE", "/parser/csv/1"),
    # parser/json
    ("GET", "/parser/json/"),
    ("GET", "/parser/json/1"),
    ("POST", "/parser/json/"),
    ("PATCH", "/parser/json/1"),
    ("DELETE", "/parser/json/1"),
    # parser/mqtt
    ("GET", "/parser/mqtt/"),
    ("GET", "/parser/mqtt/1"),
    # parser-detailed
    ("GET", "/parser-detailed/"),
    ("DELETE", "/parser-detailed/1"),
    # parser_encoding
    ("GET", "/parser_encoding/"),
    # parser_timezone
    ("GET", "/parser_timezone/"),
    # permission-group
    ("GET", "/permission-group/"),
    ("GET", "/permission-group/1"),
    # quality-control-setting
    ("GET", "/quality-control-setting/"),
    ("GET", "/quality-control-setting/1"),
    ("POST", "/quality-control-setting/"),
    ("PATCH", "/quality-control-setting/1"),
    ("DELETE", "/quality-control-setting/1"),
    # me
    ("GET", "/me/"),
]


@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS, ids=lambda x: x)
def test_no_token_returns_401(client_no_auth, method, path):
    """No Authorization header -> 401"""
    response = client_no_auth.request(method, path)
    assert response.status_code == 401


@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS, ids=lambda x: x)
def test_invalid_token_returns_401(
    client_no_auth, mock_oidc_invalid_token, method, path
):
    """Invalid Token -> OIDC ERROR -> 401"""
    response = client_no_auth.request(
        method, path, headers={"Authorization": "Bearer  invalid.token.here"}
    )
    assert response.status_code == 401
