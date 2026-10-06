import pytest

from services.ingests import build_search_params


def search(client, q=None):
    params = {"q": q} if q is not None else {}
    return client.get(
        "/ingests", params=params, headers={"authorization": "Bearer valid"}
    )


def test_requires_authorization(client, dsm_requests):
    response = client.get("/ingests", params={"q": "x"})

    assert response.status_code == 401
    assert dsm_requests == []


def test_without_query_lists_ingests(client):
    response = search(client)

    assert response.status_code == 200
    assert [i["id"] for i in response.json()["items"]] == [10, 11]


def test_search_by_name(client):
    response = search(client, "weather")

    assert response.json()["items"] == [
        {
            "id": 10,
            "uuid": "6f1c0e3a-2b5d-4c8e-9a7f-1d2e3f4a5b6c",
            "name": "Weather Station",
            "permission_group_id": 1,
            "permission_group_name": "Group One",
        }
    ]


def test_search_by_uuid(client):
    response = search(client, "0a9b8c7d-6e5f-4a3b-2c1d-0e9f8a7b6c5d")

    assert [i["id"] for i in response.json()["items"]] == [11]


def test_search_by_id_lists_exact_match_first(client):
    # "10" is the id of ingest 10 and part of the name of ingest 11
    response = search(client, "10")

    assert [i["id"] for i in response.json()["items"]] == [10, 11]


@pytest.mark.parametrize(
    "q, expected",
    [
        ("", [{"size": 20}]),
        ("abc", [{"name[ilike]": "%abc%", "size": 20}]),
        ("42", [{"id[eq]": 42}, {"name[ilike]": "%42%", "size": 20}]),
        (
            "6F1C0E3A-2B5D-4C8E-9A7F-1D2E3F4A5B6C",
            [
                {"uuid[eq]": "6f1c0e3a-2b5d-4c8e-9a7f-1d2e3f4a5b6c"},
                {
                    "name[ilike]": "%6F1C0E3A-2B5D-4C8E-9A7F-1D2E3F4A5B6C%",
                    "size": 20,
                },
            ],
        ),
    ],
)
def test_build_search_params(q, expected):
    assert build_search_params(q) == expected


def test_dsm_error_is_bad_gateway(client):
    response = client.get("/ingests", headers={"authorization": "Bearer invalid"})

    assert response.status_code == 502
