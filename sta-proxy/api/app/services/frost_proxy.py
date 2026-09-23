import logging

import httpx
from fastapi import HTTPException, Response

from config import settings

logger = logging.getLogger("app.services.frost_proxy")

# Response headers that must not be passed through 1:1
# (hop-by-hop headers, or headers httpx has already resolved, e.g. gzip).
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


def get_frost_client() -> httpx.AsyncClient:
    """Shared client for all requests (connection pooling), created lazily."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.FROST_URL.rstrip("/"),
            timeout=settings.FROST_TIMEOUT,
        )
    return _client


async def close_frost_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def frost_proxy_service(
    endpoint: str,
    query: str = "",
    accept: str | None = None,
) -> Response:
    # Keep the raw query string so FROST parameters like
    # $filter / $expand arrive exactly as the client sent them.
    url = "/" + endpoint
    if query:
        url += "?" + query

    headers = {"accept": accept} if accept else {}

    try:
        upstream = await get_frost_client().get(url, headers=headers)
    except httpx.TimeoutException:
        logger.warning("Timeout for FROST request %s", url)
        raise HTTPException(status_code=504, detail="FROST server timeout")
    except httpx.RequestError as e:
        logger.error("FROST request %s failed: %s", url, e)
        raise HTTPException(status_code=502, detail="FROST server not reachable")

    logger.debug("FROST responded with %s for %s", upstream.status_code, url)
    response_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in EXCLUDED_RESPONSE_HEADERS
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
    )
