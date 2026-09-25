import logging

import httpx
from fastapi import HTTPException

from config import settings
from models import FrostEndpoint, FrostEndpointsResponse
from services.frost_proxy import get_frost_client
from services.permission_groups import fetch_own_database_usernames

logger = logging.getLogger("app.services.frost_endpoints")


def rewrite_endpoint_url(url: str) -> str:
    """Replace the internal FROST host with the public base URL of this API.

    "http://frost.:8080/sta/<name>/v1.1" -> "<BASE_URL>/sta/<name>/v1.1"
    """
    path = httpx.URL(url).raw_path.decode()
    # strip a possible path prefix of FROST_URL (e.g. "/FROST-Server"),
    # because the proxy route adds it again when forwarding
    frost_prefix = httpx.URL(settings.FROST_URL).path.rstrip("/")
    if frost_prefix and path.startswith(frost_prefix + "/"):
        path = path[len(frost_prefix) :]
    return settings.BASE_URL.rstrip("/") + path


def rewrite_endpoint(frost_endpoint: FrostEndpoint) -> FrostEndpoint:
    frost_endpoint.url = rewrite_endpoint_url(frost_endpoint.url)
    return frost_endpoint


def matches_query(endpoint: FrostEndpoint, q: str) -> bool:
    q = q.lower()
    fields = [
        endpoint.name,
        endpoint.displayName,
        endpoint.group,
        endpoint.project or "",
    ]
    return any(q in field.lower() for field in fields)


def parse_frost_name(name: str) -> FrostEndpoint:
    """Build a FrostEndpoint from an existing FROST/database schema name,
    parsing out group/project/displayName the same way the FROST
    endpoints JSP does when listing its webapp directories."""
    first = name.find("_")
    second = name.find("_", first + 1) if first != -1 else -1

    group = name[:first] if first != -1 else name
    project = name[first + 1 : second] if second != -1 else None
    display_name = f"{group} {project}" if project else group

    url = f"{settings.BASE_URL.rstrip('/')}/sta/{name}/v1.1"

    return FrostEndpoint(
        name=name,
        displayName=display_name,
        group=group,
        project=project,
        url=url,
        is_own=True,
    )


async def frost_endpoints_service(
    q: str | None = None, authorization: str | None = None
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
        endpoints = [FrostEndpoint.model_validate(e) for e in raw_endpoints]
    except httpx.TimeoutException:
        logger.warning("Timeout while fetching FROST endpoints")
        raise HTTPException(status_code=504, detail="FROST server timeout")
    except (httpx.HTTPError, ValueError) as e:
        logger.error("Fetching FROST endpoints failed: %s", e)
        raise HTTPException(status_code=502, detail="FROST endpoints not available")

    endpoints = [rewrite_endpoint(endpoint) for endpoint in endpoints]

    if authorization:
        own_usernames = await fetch_own_database_usernames(authorization)
        existing_names = {endpoint.name for endpoint in endpoints}

        for endpoint in endpoints:
            if endpoint.name in own_usernames:
                endpoint.is_own = True

        missing_usernames = own_usernames - existing_names
        for username in missing_usernames:
            endpoints.append(parse_frost_name(username))

    if q:
        endpoints = [e for e in endpoints if matches_query(e, q)]

    logger.debug("Returning %s FROST endpoints", len(endpoints))
    return FrostEndpointsResponse(endpoints=endpoints)
