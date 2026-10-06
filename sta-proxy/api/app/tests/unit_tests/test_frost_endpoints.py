import pytest

from config import settings
from models import FrostEndpoint
from services.frost_endpoints import (
    endpoint_from_frost,
    matches_query,
    parse_frost_name,
    rewrite_endpoint_url,
)


@pytest.mark.parametrize("path", ["/endpoints", "/endpoints/"])
def test_endpoints_uses_configured_base_url(client, path):
    response = client.get(path)
    assert response.status_code == 200
    endpoints = response.json()["endpoints"]
    assert len(endpoints) == 2
    assert endpoints[0]["url"] == (
        f"{settings.BASE_URL}/sta/vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb/v1.1"
    )
    assert endpoints[1]["name"] == "vo_group2_86ebe19a704a496ca2c8053c2c6c3c17"
    assert endpoints[1]["display_name"] == "GROUP2"


def test_endpoints_uses_updated_base_url_setting(client, monkeypatch):
    monkeypatch.setattr(settings, "BASE_URL", "https://example.org")
    response = client.get("/endpoints")
    assert response.json()["endpoints"][0]["url"] == (
        "https://example.org/sta/vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb/v1.1"
    )


def test_rewrite_strips_frost_url_prefix(monkeypatch):
    monkeypatch.setattr(settings, "FROST_URL", "http://frost:8080/FROST-Server")
    monkeypatch.setattr(settings, "BASE_URL", "http://localhost")
    assert (
        rewrite_endpoint_url("http://frost.:8080/FROST-Server/sta/x/v1.1")
        == "http://localhost/sta/x/v1.1"
    )


def test_endpoints_marks_internal_and_adds_missing(client):
    response = client.get("/endpoints", headers={"authorization": "Bearer valid"})

    internal = [e for e in response.json()["endpoints"] if e["is_internal"]]
    assert [e["name"] for e in internal] == [
        "vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb",
        "vo_group3_0f1e2d3c4b5a69788796a5b4c3d2e1f0",
    ]


def test_endpoints_display_name_is_same_for_internal_and_public(client):
    public = client.get("/endpoints").json()["endpoints"]
    authenticated = client.get(
        "/endpoints", headers={"authorization": "Bearer valid"}
    ).json()["endpoints"]

    public_names = {e["name"]: e["display_name"] for e in public}
    names = {e["name"]: (e["display_name"], e["is_internal"]) for e in authenticated}
    assert public_names == {
        "vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb": "GROUP1",
        "vo_group2_86ebe19a704a496ca2c8053c2c6c3c17": "GROUP2",
    }
    assert names == {
        "vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb": ("GROUP1", True),
        "vo_group2_86ebe19a704a496ca2c8053c2c6c3c17": ("GROUP2", False),
        # not listed by FROST yet, added from the user's permission groups
        "vo_group3_0f1e2d3c4b5a69788796a5b4c3d2e1f0": ("GROUP3", True),
    }


def test_endpoints_q_matches_added_internal_endpoint(client):
    response = client.get(
        "/endpoints",
        params={"q": "group_3"},
        headers={"authorization": "Bearer valid"},
    )

    assert [e["name"] for e in response.json()["endpoints"]] == [
        "vo_group3_0f1e2d3c4b5a69788796a5b4c3d2e1f0"
    ]


def test_endpoints_filtered_by_ingest_id(client):
    response = client.get(
        "/endpoints",
        params={"ingest_id": 11},
        headers={"authorization": "Bearer valid"},
    )

    assert [e["name"] for e in response.json()["endpoints"]] == [
        "vo_group3_0f1e2d3c4b5a69788796a5b4c3d2e1f0"
    ]


def test_endpoints_filtered_by_unknown_ingest_id_is_empty(client):
    response = client.get(
        "/endpoints",
        params={"ingest_id": 999},
        headers={"authorization": "Bearer valid"},
    )

    assert response.json()["endpoints"] == []


@pytest.mark.parametrize(
    "q, expected",
    [
        ("group2", True),
        ("GROUP2", True),
        ("Group_2", True),
        ("gro_up", True),
        ("group3", False),
        # the VO prefix is not part of the display name
        ("vo", False),
    ],
)
def test_matches_query_is_fuzzy(q, expected):
    endpoint = FrostEndpoint(
        name="vo_group2_86ebe19a704a496ca2c8053c2c6c3c17",
        display_name="GROUP2",
        group="vo",
        project="group2",
        url="http://localhost/sta/vo_group2_86ebe19a704a496ca2c8053c2c6c3c17/v1.1",
    )
    assert matches_query(endpoint, q) is expected


def test_endpoints_q_is_fuzzy(client):
    response = client.get("/endpoints", params={"q": "Group_2"})

    assert [e["name"] for e in response.json()["endpoints"]] == [
        "vo_group2_86ebe19a704a496ca2c8053c2c6c3c17"
    ]


def test_parse_frost_name_uses_uppercase_group():
    endpoint = parse_frost_name("vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb")

    assert endpoint.display_name == "GROUP1"
    assert endpoint.group == "vo"
    assert endpoint.project == "group1"


def test_endpoint_from_frost_ignores_frost_display_name():
    endpoint = endpoint_from_frost(
        {
            "name": "vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb",
            "displayName": "vo group1",
            "group": "vo",
            "project": "group1",
            "url": "http://frost.:8080/sta/vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb/v1.1",
        }
    )

    assert endpoint.display_name == "GROUP1"
    assert endpoint.url == (
        f"{settings.BASE_URL}/sta/vo_group1_82ed8cbd57aa4ba6b8b12fcc01650bbb/v1.1"
    )


def test_endpoint_from_frost_rejects_missing_url():
    with pytest.raises(ValueError):
        endpoint_from_frost({"name": "vo_group1", "group": "vo"})
