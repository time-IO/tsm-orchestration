import httpx

import services.frost_proxy as frost_proxy


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
        frost_proxy,
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
