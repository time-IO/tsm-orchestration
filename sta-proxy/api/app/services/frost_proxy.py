import logging

import httpx
from fastapi import HTTPException, Response

from config import settings
from services.permission_groups import (
    fetch_own_permission_groups,
    has_internal_access,
)

logger = logging.getLogger("app.services.frost_proxy")

EXCLUDED_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "transfer-encoding",
    "content-encoding",
    "content-length",
    "server",
    "date",
}

_client: httpx.AsyncClient | None = None
_internal_client: httpx.AsyncClient | None = None


def get_frost_client() -> httpx.AsyncClient:
    """Shared client for all requests (connection pooling), created lazily."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.FROST_URL.rstrip("/"),
            timeout=settings.FROST_TIMEOUT,
        )
    return _client


def get_frost_internal_client() -> httpx.AsyncClient:
    """Shared client for requests to the internal FROST, created lazily."""
    global _internal_client
    if _internal_client is None or _internal_client.is_closed:
        _internal_client = httpx.AsyncClient(
            base_url=settings.FROST_INTERNAL_URL.rstrip("/"),
            timeout=settings.FROST_TIMEOUT,
        )
    return _internal_client


async def close_frost_client() -> None:
    global _client, _internal_client
    if _client is not None:
        await _client.aclose()
        _client = None
    if _internal_client is not None:
        await _internal_client.aclose()
        _internal_client = None


async def select_frost_client(
    endpoint: str, authorization: str | None
) -> tuple[httpx.AsyncClient, bool]:

    if authorization:
        name = endpoint.strip("/").split("/", 1)[0]
        permission_groups = await fetch_own_permission_groups(authorization)
        if has_internal_access(name, permission_groups):
            logger.debug("Forwarding %s to internal FROST", endpoint)
            return get_frost_internal_client(), True
    return get_frost_client(), False


async def fetch_from_frost(
    url: str, headers: dict[str, str], client: httpx.AsyncClient | None = None
) -> httpx.Response:
    client = client or get_frost_client()
    try:
        return await client.get(url, headers=headers)
    except httpx.TimeoutException:
        logger.warning("Timeout for FROST request %s", url)
        raise HTTPException(status_code=504, detail="FROST server timeout")
    except httpx.RequestError as e:
        logger.error("FROST request %s failed: %s", url, e)
        raise HTTPException(status_code=502, detail="FROST server not reachable")


def to_response(upstream: httpx.Response, internal: bool = False) -> Response:
    """Pass the FROST response through, minus hop-by-hop/resolved headers."""
    response_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in EXCLUDED_RESPONSE_HEADERS
    }
    # the response depends on who is asking (internal vs. public FROST)
    response_headers["vary"] = ", ".join(
        v for v in (response_headers.pop("vary", None), "Authorization") if v
    )
    if internal:
        # never let shared caches serve internal data to someone else
        response_headers["cache-control"] = "private, no-store"
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
    )


async def frost_proxy_service(
    endpoint: str,
    query: str = "",
    accept: str | None = None,
    authorization: str | None = None,
) -> Response:
    url = "/" + endpoint
    if query:
        url += "?" + query

    headers = {"accept": accept} if accept else {}
    client, internal = await select_frost_client(endpoint, authorization)
    upstream = await fetch_from_frost(url, headers, client)
    logger.debug("FROST responded with %s for %s", upstream.status_code, url)
    return to_response(upstream, internal)
