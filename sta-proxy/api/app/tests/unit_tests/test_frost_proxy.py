import json

import httpx
import pytest
from cachetools import TTLCache
from fastapi import HTTPException

import services.dsm_api as dsm_api
import services.frost_proxy as frost_proxy
import services.permission_groups as permission_groups
from routers.frost_proxy import validate_proxied_path
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


@pytest.mark.parametrize(
    "endpoint, status_code",
    [
        ("..", 400),
        ("a/../b", 400),
        ("a/b/..", 400),
        ("", 404),
        ("/", 404),
    ],
)
def test_validate_proxied_path_rejects(endpoint, status_code):
    with pytest.raises(HTTPException) as exc:
        validate_proxied_path(endpoint)
    assert exc.value.status_code == status_code


@pytest.mark.parametrize(
    "endpoint",
    [f"{OWN_ENDPOINT}/v1.1/Things", f"{OWN_ENDPOINT}/v1.1", "a..b/v1.1"],
)
def test_validate_proxied_path_accepts(endpoint):
    validate_proxied_path(endpoint)


def test_permission_groups_are_cached_per_token(client, dsm_requests):
    for skip in (0, 100, 200):
        client.get(
            f"/{OWN_ENDPOINT}/v1.1/Things?$skip={skip}",
            headers={"authorization": "Bearer valid"},
        )
    assert len(dsm_requests) == 1


def test_permission_groups_cache_expires(client, dsm_requests, monkeypatch):
    now = [0.0]
    monkeypatch.setattr(permission_groups, "_cache", TTLCache(8, 60, lambda: now[0]))
    headers = {"authorization": "Bearer valid"}
    client.get(f"/{OWN_ENDPOINT}/v1.1", headers=headers)
    now[0] = 59
    client.get(f"/{OWN_ENDPOINT}/v1.1", headers=headers)
    assert len(dsm_requests) == 1
    now[0] = 61
    client.get(f"/{OWN_ENDPOINT}/v1.1", headers=headers)
    assert len(dsm_requests) == 2


def test_failed_permission_groups_lookup_is_not_cached(
    client, dsm_requests, frost_requests, frost_internal_requests
):
    for _ in range(2):
        client.get(f"/{OWN_ENDPOINT}/v1.1", headers={"authorization": "Bearer invalid"})
    assert len(dsm_requests) == 2
    assert frost_internal_requests == []
    assert len(frost_requests) == 2


def test_public_route_forwards_to_public_frost_without_dsm_check(
    client, frost_requests, frost_internal_requests, dsm_requests
):
    response = client.get(
        f"/public/{OWN_ENDPOINT}/v1.1/Things?$top=1",
        headers={"authorization": "Bearer valid"},
    )
    assert response.status_code == 200
    assert "cache-control" not in response.headers
    assert frost_requests[0].url.raw_path.decode() == (
        f"/{OWN_ENDPOINT}/v1.1/Things?$top=1"
    )
    assert "authorization" not in frost_requests[0].headers
    assert frost_internal_requests == []
    assert dsm_requests == []


def test_internal_route_forwards_owner_to_internal_frost(
    client, frost_requests, frost_internal_requests
):
    response = client.get(
        f"/internal/{OWN_ENDPOINT}/v1.1/Things?$top=1",
        headers={"authorization": "Bearer valid"},
    )
    assert response.status_code == 200
    assert response.json()["internal"] is True
    assert response.headers["cache-control"] == "private, no-store"
    assert frost_internal_requests[0].url.raw_path.decode() == (
        f"/{OWN_ENDPOINT}/v1.1/Things?$top=1"
    )
    assert "authorization" not in frost_internal_requests[0].headers
    assert frost_requests == []


def test_internal_route_accepts_session_cookie(client, frost_internal_requests):
    client.cookies.set("sta_session", "valid")
    response = client.get(f"/internal/{OWN_ENDPOINT}/v1.1")
    assert response.status_code == 200
    assert len(frost_internal_requests) == 1


@pytest.mark.parametrize(
    "endpoint, headers, status_code",
    [
        (OWN_ENDPOINT, {}, 401),
        (OWN_ENDPOINT, {"authorization": "Bearer invalid"}, 401),
        (FOREIGN_ENDPOINT, {"authorization": "Bearer valid"}, 403),
        (f"{OWN_ENDPOINT}x", {"authorization": "Bearer valid"}, 403),
    ],
)
def test_internal_route_rejects_without_access(
    client, frost_requests, frost_internal_requests, endpoint, headers, status_code
):
    response = client.get(f"/internal/{endpoint}/v1.1", headers=headers)
    assert response.status_code == status_code
    assert frost_requests == []
    assert frost_internal_requests == []


@pytest.mark.parametrize(
    "error, status_code",
    [
        (httpx.ConnectError("connection refused"), 502),
        (httpx.ReadTimeout("timeout"), 504),
    ],
)
def test_internal_route_dsm_not_available(
    client, monkeypatch, frost_requests, frost_internal_requests, error, status_code
):
    def handler(request):
        raise error

    monkeypatch.setattr(
        dsm_api,
        "_client",
        httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://dsm-api"
        ),
    )
    response = client.get(
        f"/internal/{OWN_ENDPOINT}/v1.1", headers={"authorization": "Bearer valid"}
    )
    # no silent fallback to the public data
    assert response.status_code == status_code
    assert frost_requests == []
    assert frost_internal_requests == []


@pytest.mark.parametrize("prefix", ["public", "internal"])
@pytest.mark.parametrize(
    "endpoint, status_code", [("", 404), ("a/%2E%2E/%2E%2E/x", 400)]
)
def test_explicit_routes_validate_path(
    client, frost_requests, frost_internal_requests, prefix, endpoint, status_code
):
    response = client.get(
        f"/{prefix}/{endpoint}", headers={"authorization": "Bearer valid"}
    )
    assert response.status_code == status_code
    assert frost_requests == []
    assert frost_internal_requests == []


STA_ROOT = "http://host/sta/"


@pytest.fixture(autouse=True)
def sta_proxy_url(monkeypatch):
    # independent of the STA_PROXY_URL of the environment running the tests
    monkeypatch.setattr(frost_proxy.settings, "STA_PROXY_URL", STA_ROOT)


def frost_with_links(monkeypatch, server, content_type="application/json"):
    def handler(request: httpx.Request) -> httpx.Response:
        root = f"{STA_ROOT}{OWN_ENDPOINT}/v1.1"
        body = json.dumps(
            {
                "@iot.nextLink": f"{root}/Things?$skip=100",
                "value": [
                    {
                        "@iot.selfLink": f"{root}/Things(1)",
                        "Datastreams@iot.navigationLink": f"{root}/Things(1)/Datastreams",
                        "properties": {"other": f"{STA_ROOT}{OWN_ENDPOINT}x/v1.1"},
                    }
                ],
            }
        )
        return httpx.Response(
            200, content=body.encode(), headers={"content-type": content_type}
        )

    monkeypatch.setattr(
        server,
        "_client",
        httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://x"),
    )


@pytest.mark.parametrize(
    "route, server",
    [("public", frost_proxy.public_frost), ("internal", frost_proxy.internal_frost)],
)
def test_explicit_routes_rewrite_links(client, monkeypatch, route, server):
    frost_with_links(monkeypatch, server)
    response = client.get(
        f"/{route}/{OWN_ENDPOINT}/v1.1/Things",
        headers={"authorization": "Bearer valid"},
    )
    root = f"{STA_ROOT}{route}/{OWN_ENDPOINT}/v1.1"
    data = response.json()
    assert data["@iot.nextLink"] == f"{root}/Things?$skip=100"
    assert data["value"][0]["@iot.selfLink"] == f"{root}/Things(1)"
    assert data["value"][0]["Datastreams@iot.navigationLink"] == (
        f"{root}/Things(1)/Datastreams"
    )
    # other endpoints sharing the name as prefix are untouched
    assert data["value"][0]["properties"]["other"] == f"{STA_ROOT}{OWN_ENDPOINT}x/v1.1"
    assert int(response.headers["content-length"]) == len(response.content)


def test_automatic_route_does_not_rewrite_links(client, monkeypatch):
    frost_with_links(monkeypatch, frost_proxy.internal_frost)
    response = client.get(
        f"/{OWN_ENDPOINT}/v1.1/Things", headers={"authorization": "Bearer valid"}
    )
    assert response.json()["@iot.nextLink"] == (
        f"{STA_ROOT}{OWN_ENDPOINT}/v1.1/Things?$skip=100"
    )


def test_non_json_response_is_not_rewritten(client, monkeypatch):
    frost_with_links(monkeypatch, frost_proxy.public_frost, "text/csv")
    response = client.get(f"/public/{OWN_ENDPOINT}/v1.1/Things")
    assert f"{STA_ROOT}{OWN_ENDPOINT}/v1.1" in response.text
    assert "/public/" not in response.text


def test_large_response_is_rewritten_in_thread(client, monkeypatch):
    monkeypatch.setattr(frost_proxy, "REWRITE_IN_THREAD_MIN_SIZE", 0)
    frost_with_links(monkeypatch, frost_proxy.public_frost)
    response = client.get(f"/public/{OWN_ENDPOINT}/v1.1/Things")
    assert response.json()["@iot.nextLink"] == (
        f"{STA_ROOT}public/{OWN_ENDPOINT}/v1.1/Things?$skip=100"
    )


@pytest.mark.parametrize(
    "sta_proxy_url, frost_root",
    [
        # FROST appends the name to STA_PROXY_URL as is
        ("http://host/sta", f"http://host/sta{OWN_ENDPOINT}/"),
        ("http://host/sta/", f"http://host/sta/{OWN_ENDPOINT}/"),
    ],
)
def test_get_link_rewrite(monkeypatch, sta_proxy_url, frost_root):
    monkeypatch.setattr(frost_proxy.settings, "STA_PROXY_URL", sta_proxy_url)
    assert frost_proxy.get_link_rewrite(f"{OWN_ENDPOINT}/v1.1/Things", "internal") == (
        frost_root.encode(),
        f"http://host/sta/internal/{OWN_ENDPOINT}/".encode(),
    )
