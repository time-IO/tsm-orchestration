import hashlib
import logging

import httpx
from cachetools import TTLCache

from config import settings
from services.dsm_api import fetch_dsm_api

logger = logging.getLogger("app.services.permission_groups")

_cache: TTLCache[str, dict[str, dict]] = TTLCache(
    maxsize=settings.PERMISSION_GROUPS_CACHE_SIZE,
    ttl=settings.PERMISSION_GROUPS_CACHE_TTL,
)


def _cache_key(authorization: str) -> str:
    return hashlib.sha256(authorization.encode()).hexdigest()


def clear_permission_groups_cache() -> None:
    _cache.clear()


async def fetch_own_permission_groups(authorization: str) -> dict[str, dict]:
    key = _cache_key(authorization)
    cached = _cache.get(key)
    if cached is not None:
        logger.debug("Using cached permission groups")
        return cached

    try:
        data = await fetch_dsm_api("/permission-group/", authorization)
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Fetching own permission groups failed: %s", e)
        return {}

    items = data.get("items", []) if isinstance(data, dict) else []
    permission_groups = {
        item["database_username"]: item
        for item in items
        if item.get("database_username")
    }
    _cache[key] = permission_groups
    return permission_groups


def has_internal_access(endpoint_name: str, permission_groups: dict[str, dict]) -> bool:
    return endpoint_name in permission_groups
