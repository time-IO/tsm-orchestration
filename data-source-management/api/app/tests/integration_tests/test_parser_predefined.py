"""Read-only predefined parsers and persisted selections on file ingests."""

import pytest

BASE_PATH = "/parser/predefined"


def get_truelog(client):
    response = client.get(f"{BASE_PATH}/", params={"recommended_for": "file"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    parser = items[0]
    assert parser["name"] == "truelog100"
    assert parser["parser_type"] == "predefined"
    assert set(parser) == {"id", "uuid", "parser_type", "name"}
    return parser


@pytest.mark.parametrize("client_fixture", ["client", "client_other_group"])
def test_shared_parser_is_readable(request, client_fixture):
    client = request.getfixturevalue(client_fixture)
    parser = get_truelog(client)
    assert client.get(f"{BASE_PATH}/{parser['id']}").json() == parser


def test_mqtt_endpoint_preserves_existing_implementations(client):
    items = client.get("/parser/mqtt/").json()["items"]
    assert {p["name"] for p in items} == {
        "campbell_cr6",
        "ydoc_ml417",
        "chirpstack_generic",
        "quaesta",
    }
    assert all(p["parser_type"] == "predefined" for p in items)
    for parser in items:
        assert client.get(f"/parser/mqtt/{parser['id']}").json() == parser
    truelog = get_truelog(client)
    assert client.get(f"/parser/mqtt/{truelog['id']}").status_code == 404
    all_items = client.get(f"{BASE_PATH}/").json()["items"]
    assert {p["id"] for p in all_items} == {p["id"] for p in items} | {truelog["id"]}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_no_predefined_mutation_endpoints(client, method):
    parser = get_truelog(client)
    path = f"{BASE_PATH}/" if method == "post" else f"{BASE_PATH}/{parser['id']}"
    assert client.request(method, path, json={"name": "changed"}).status_code == 405
    assert get_truelog(client) == parser


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("delete", "/parser-detailed"),
        ("patch", "/parser/csv"),
        ("patch", "/parser/json"),
        ("patch", "/parser/soilcan"),
    ],
)
def test_user_managed_routes_cannot_mutate_predefined_parser(client, method, path):
    parser = get_truelog(client)
    assert (
        client.request(
            method, f"{path}/{parser['id']}", json={"name": "changed"}
        ).status_code
        == 404
    )
    assert get_truelog(client) == parser


def test_requires_authentication(client_no_auth):
    assert client_no_auth.get(f"{BASE_PATH}/").status_code == 401


def test_missing_parser(client):
    assert client.get(f"{BASE_PATH}/99999999").status_code == 404


@pytest.mark.parametrize(
    ("ingest_type", "extra"),
    [
        ("sftp", {}),
        ("http", {"file_type": "csv", "api_key": "test-api-key"}),
        ("external-sftp", {"uri": "sftp://example.com", "path": "/data"}),
    ],
)
def test_file_ingest_selection_round_trip(
    client, base_data, cleanup_ingest, ingest_type, extra
):
    parser = get_truelog(client)
    payload = {
        "name": "Predefined file ingest",
        "permission_group_id": base_data["permission_group_id"],
        "parser_id": parser["id"],
        "filename_pattern": "*.csv",
        **extra,
    }
    response = client.post(f"/ingest/{ingest_type}/", json=payload)
    assert response.status_code == 200, response.text
    ingest_id = response.json()["id"]
    saved = client.get(f"/ingest/{ingest_type}/{ingest_id}").json()
    assert saved["parser_id"] == parser["id"]
    assert saved["parser"] == {k: parser[k] for k in ("id", "name", "parser_type")}
    for parser_id in (base_data["parser_id"], parser["id"]):
        response = client.patch(
            f"/ingest/{ingest_type}/{ingest_id}",
            json={
                "parser_id": parser_id,
                "permission_group_id": base_data["permission_group_id"],
            },
        )
        assert response.status_code == 200, response.text
        assert (
            client.get(f"/ingest/{ingest_type}/{ingest_id}").json()["parser_id"]
            == parser_id
        )
    assert (
        client.get(f"/ingest/{ingest_type}/{ingest_id}").json()["parser"]
        == saved["parser"]
    )


def test_recommendations_do_not_restrict_api_selections(
    client, base_data, cleanup_ingest
):
    mqtt_parser = client.get("/parser/mqtt/").json()["items"][0]
    response = client.post(
        "/ingest/sftp/",
        json={
            "name": "Future combination",
            "permission_group_id": base_data["permission_group_id"],
            "parser_id": mqtt_parser["id"],
            "filename_pattern": "*.json",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["parser_id"] == mqtt_parser["id"]
