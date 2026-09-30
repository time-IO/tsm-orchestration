import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger("app.services.dsm_api")

_client: httpx.AsyncClient | None = None


def get_dsm_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.DSM_API_URL.rstrip("/"),
            timeout=settings.DSM_API_TIMEOUT,
        )
    return _client


async def close_dsm_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def fetch_dsm_api(
    path: str,
    authorization: str,
    params: dict[str, Any] | None = None,
) -> Any:
    response = await get_dsm_client().get(
        path,
        headers={"authorization": authorization, "accept": "application/json"},
        params=params,
    )
    logger.debug("DSM API responded with %s for %s", response.status_code, path)
    response.raise_for_status()
    return response.json()
