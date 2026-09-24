import logging

import httpx
from fastapi import HTTPException

from config import settings
from models import FrostEndpoint, FrostEndpointsResponse
from services.frost_proxy import get_frost_client

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


async def frost_endpoints_service(q: str | None = None) -> FrostEndpointsResponse:
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

    if q:
        endpoints = [e for e in endpoints if matches_query(e, q)]

    logger.debug("Returning %s FROST endpoints", len(endpoints))
    return FrostEndpointsResponse(endpoints=endpoints)
