import httpx
import pytest

import services.frost_proxy as frost_proxy
from services.frost_proxy import get_endpoint_name_from_proxied_path


def test_forwards_path(client, frost_requests):
    response = client.get("/v1.1/Things")
    assert response.status_code == 200
    assert response.json() == {"value": []}
    assert str(frost_requests[0].url) == "http://frost:8080/v1.1/Things"


def test_forwards_query_unchanged(client, frost_requests):
    query = "$filter=name%20eq%20%27a%20b%27&$expand=Observations($top=1)"
    client.get(f"/v1.1/Things(1)/Datastreams?{query}")
    assert frost_requests[0].url.raw_path.decode() == (
        f"/v1.1/Things(1)/Datastreams?{query}"
    )


def test_nested_endpoint_with_param(client, frost_requests):
    client.get("/endpoint/folder?param=foo")
    assert frost_requests[0].url.raw_path == b"/endpoint/folder?param=foo"


def test_passes_through_status_code(client):
    response = client.get("/missing")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/json"


def test_rejects_path_traversal(client, frost_requests):
    response = client.get("/a/%2E%2E/%2E%2E/x")
    assert response.status_code == 400
    assert frost_requests == []


def test_frost_not_reachable(client, monkeypatch):
    def handler(request):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(
        frost_proxy.public_frost,
        "_client",
        httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://frost"
        ),
    )
    response = client.get("/v1.1")
    assert response.status_code == 502


def test_frost_root_is_blocked(client, frost_requests):
    assert client.get("/").status_code == 404
    assert frost_requests == []


def test_sta_endpoint_is_forwarded(client, frost_requests):
    response = client.get("/sta/vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb/v1.1/Things")
    assert response.status_code == 200
    assert frost_requests[0].url.path == (
        "/sta/vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb/v1.1/Things"
    )


OWN_ENDPOINT = "vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb"
FOREIGN_ENDPOINT = "vo_group2_86ebe19a704a496ca2c8053c2c6c3c17"


def test_owner_is_forwarded_to_internal_frost(
    client, frost_requests, frost_internal_requests
):
    response = client.get(
        f"/{OWN_ENDPOINT}/v1.1/Things?$top=1",
        headers={"authorization": "Bearer valid"},
    )
    assert response.status_code == 200
    assert response.json()["internal"] is True
    assert frost_requests == []
    assert frost_internal_requests[0].url.raw_path.decode() == (
        f"/{OWN_ENDPOINT}/v1.1/Things?$top=1"
    )


def test_authorization_is_not_forwarded_to_frost(client, frost_internal_requests):
    client.get(f"/{OWN_ENDPOINT}/v1.1", headers={"authorization": "Bearer valid"})
    assert "authorization" not in frost_internal_requests[0].headers


def test_anonymous_is_forwarded_to_public_frost(
    client, frost_requests, frost_internal_requests, dsm_requests
):
    client.get(f"/{OWN_ENDPOINT}/v1.1/Things")
    assert frost_internal_requests == []
    assert frost_requests[0].url.path == f"/{OWN_ENDPOINT}/v1.1/Things"
    assert dsm_requests == []


def test_invalid_token_is_forwarded_to_public_frost(
    client, frost_requests, frost_internal_requests
):
    client.get(f"/{OWN_ENDPOINT}/v1.1", headers={"authorization": "Bearer invalid"})
    assert frost_internal_requests == []
    assert len(frost_requests) == 1


def test_non_owner_is_forwarded_to_public_frost(
    client, frost_requests, frost_internal_requests
):
    client.get(f"/{FOREIGN_ENDPOINT}/v1.1", headers={"authorization": "Bearer valid"})
    assert frost_internal_requests == []
    assert frost_requests[0].url.path == f"/{FOREIGN_ENDPOINT}/v1.1"


def test_endpoint_name_must_match_exactly(client, frost_internal_requests):
    client.get(f"/{OWN_ENDPOINT}x/v1.1", headers={"authorization": "Bearer valid"})
    client.get(f"/x/{OWN_ENDPOINT}/v1.1", headers={"authorization": "Bearer valid"})
    assert frost_internal_requests == []


def test_response_varies_by_authorization(client):
    response = client.get(f"/{OWN_ENDPOINT}/v1.1")
    assert "authorization" in response.headers["vary"].lower()


def test_internal_frost_not_reachable(client, monkeypatch, frost_requests):
    def handler(request):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(
        frost_proxy.internal_frost,
        "_client",
        httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://frost-internal"
        ),
    )
    response = client.get(
        f"/{OWN_ENDPOINT}/v1.1", headers={"authorization": "Bearer valid"}
    )
    # no silent fallback to the public data
    assert response.status_code == 502
    assert frost_requests == []


@pytest.mark.parametrize(
    "endpoint, expected",
    [
        (f"{OWN_ENDPOINT}/v1.1/Things", OWN_ENDPOINT),
        (f"/{OWN_ENDPOINT}/v1.1", OWN_ENDPOINT),
        (f"{OWN_ENDPOINT}/", OWN_ENDPOINT),
        (OWN_ENDPOINT, OWN_ENDPOINT),
        ("", ""),
    ],
)
def test_get_endpoint_name(endpoint, expected):
    assert get_endpoint_name_from_proxied_path(endpoint) == expected


def test_public_response_is_cacheable(client):
    response = client.get(f"/{OWN_ENDPOINT}/v1.1")
    assert "cache-control" not in response.headers
    assert "authorization" in response.headers["vary"].lower()


def test_internal_response_is_private(client):
    response = client.get(
        f"/{OWN_ENDPOINT}/v1.1", headers={"authorization": "Bearer valid"}
    )
    assert response.headers["cache-control"] == "private, no-store"
