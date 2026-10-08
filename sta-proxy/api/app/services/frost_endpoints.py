import logging

import httpx
from fastapi import HTTPException

from config import settings
from models import FrostEndpoint, FrostEndpointsResponse
from services.frost_proxy import get_frost_client
from services.ingests import fetch_ingest_permission_group_id
from services.permission_groups import fetch_own_permission_groups

logger = logging.getLogger("app.services.frost_endpoints")


def rewrite_endpoint_url(url: str) -> str:
    """Replace the internal FROST host with the public base URL of this API.
    "http://frost.:8080/sta/<name>/v1.1" -> "<BASE_URL>/sta/<name>/v1.1"
    """
    path = httpx.URL(url).raw_path.decode()
    # strip possible path prefix of FROST_URL as proxy route adds it when forwarding
    frost_prefix = httpx.URL(settings.FROST_URL).path.rstrip("/")
    if frost_prefix and path.startswith(frost_prefix + "/"):
        path = path[len(frost_prefix) :]
    return settings.BASE_URL.rstrip("/") + path


def frost_display_name(group: str, project: str | None) -> str:
    return (project or group).upper()


def endpoint_from_frost(raw: dict) -> FrostEndpoint:
    """Build a FrostEndpoint from an entry of the FROST endpoints listing."""
    group = raw.get("group")
    project = raw.get("project")
    endpoint = FrostEndpoint.model_validate(
        {
            "name": raw.get("name"),
            "display_name": frost_display_name(group or "", project),
            "group": group,
            "project": project,
            "url": raw.get("url"),
        }
    )
    endpoint.url = rewrite_endpoint_url(endpoint.url)
    return endpoint


def normalize_search(value: str) -> str:
    return value.replace("_", "").casefold()


def matches_query(endpoint: FrostEndpoint, q: str) -> bool:
    return normalize_search(q) in normalize_search(endpoint.display_name)


async def fetch_frost_endpoints() -> list[FrostEndpoint]:
    """Fetch the public endpoint listing from FROST."""
    try:
        upstream = await get_frost_client().get(
            settings.FROST_ENDPOINTS_PATH,
            headers={"accept": "application/json"},
            follow_redirects=True,
        )
        upstream.raise_for_status()
        data = upstream.json()
        raw_endpoints = data.get("endpoints", []) if isinstance(data, dict) else []
        return [endpoint_from_frost(e) for e in raw_endpoints]
    except httpx.TimeoutException:
        logger.warning("Timeout while fetching FROST endpoints")
        raise HTTPException(status_code=504, detail="FROST server timeout")
    except (httpx.HTTPError, ValueError) as e:
        logger.error("Fetching FROST endpoints failed: %s", e)
        raise HTTPException(status_code=502, detail="FROST endpoints not available")


def mark_internal_endpoints(
    endpoints: list[FrostEndpoint], permission_groups: dict[str, dict]
) -> list[FrostEndpoint]:
    """Mark endpoints the user has a permission group for as internal and
    show them first."""
    for endpoint in endpoints:
        if endpoint.name in permission_groups:
            endpoint.is_internal = True
    return sorted(endpoints, key=lambda e: not e.is_internal)


async def filter_by_ingest(
    endpoints: list[FrostEndpoint],
    permission_groups: dict[str, dict],
    authorization: str,
    ingest_id: int,
) -> list[FrostEndpoint]:
    """Keep only the endpoint belonging to the permission group of the ingest."""
    permission_group_id = await fetch_ingest_permission_group_id(
        authorization, ingest_id
    )
    if permission_group_id is None:
        return []
    return [
        e
        for e in endpoints
        if permission_groups.get(e.name, {}).get("id") == permission_group_id
    ]


async def frost_endpoints_service(
    q: str | None = None,
    authorization: str | None = None,
    ingest_id: int | None = None,
) -> FrostEndpointsResponse:
    endpoints = await fetch_frost_endpoints()

    if authorization:
        permission_groups = await fetch_own_permission_groups(authorization)
        endpoints = mark_internal_endpoints(endpoints, permission_groups)
        if ingest_id is not None:
            endpoints = await filter_by_ingest(
                endpoints, permission_groups, authorization, ingest_id
            )

    if q:
        endpoints = [e for e in endpoints if matches_query(e, q)]

    logger.debug("Returning %s FROST endpoints", len(endpoints))
    return FrostEndpointsResponse(endpoints=endpoints)
