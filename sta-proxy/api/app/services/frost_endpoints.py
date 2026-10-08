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


def parse_frost_name(name: str) -> FrostEndpoint:
    first = name.find("_")
    second = name.find("_", first + 1) if first != -1 else -1

    group = name[:first] if first != -1 else name
    project = name[first + 1 : second] if second != -1 else None
    display_name = frost_display_name(group, project)

    url = f"{settings.BASE_URL.rstrip('/')}/sta/{name}/v1.1"

    return FrostEndpoint(
        name=name,
        display_name=display_name,
        group=group,
        project=project,
        url=url,
        is_internal=True,
    )


async def frost_endpoints_service(
    q: str | None = None,
    authorization: str | None = None,
    ingest_id: int | None = None,
) -> FrostEndpointsResponse:
    try:
        upstream = await get_frost_client().get(
            settings.FROST_ENDPOINTS_PATH,
            headers={"accept": "application/json"},
            follow_redirects=True,
        )
        upstream.raise_for_status()
        data = upstream.json()
        raw_endpoints = data.get("endpoints", []) if isinstance(data, dict) else []
        endpoints = [endpoint_from_frost(e) for e in raw_endpoints]
    except httpx.TimeoutException:
        logger.warning("Timeout while fetching FROST endpoints")
        raise HTTPException(status_code=504, detail="FROST server timeout")
    except (httpx.HTTPError, ValueError) as e:
        logger.error("Fetching FROST endpoints failed: %s", e)
        raise HTTPException(status_code=502, detail="FROST endpoints not available")

    if authorization:
        permission_groups = await fetch_own_permission_groups(authorization)
        existing_names = {endpoint.name for endpoint in endpoints}

        for username in permission_groups:
            if username not in existing_names:
                endpoints.append(parse_frost_name(username))

        for endpoint in endpoints:
            if endpoint.name in permission_groups:
                endpoint.is_internal = True

        # show internal endpoints first
        endpoints.sort(key=lambda e: not e.is_internal)

        if ingest_id is not None:
            permission_group_id = await fetch_ingest_permission_group_id(
                authorization, ingest_id
            )
            endpoints = [
                e
                for e in endpoints
                if permission_group_id is not None
                and permission_groups.get(e.name, {}).get("id") == permission_group_id
            ]

    if q:
        endpoints = [e for e in endpoints if matches_query(e, q)]

    logger.debug("Returning %s FROST endpoints", len(endpoints))
    return FrostEndpointsResponse(endpoints=endpoints)
