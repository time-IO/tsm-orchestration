import pytest

from config import settings
from services.frost_endpoints import rewrite_endpoint_url


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
    assert endpoints[1]["displayName"] == "vo group2"


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
