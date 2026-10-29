import hashlib
import logging

from cachetools import TTLCache
from fastapi import HTTPException

from config import settings
from services.dsm_api import fetch_dsm_api_or_raise, get_items

logger = logging.getLogger("app.services.permission_groups")

_cache: TTLCache[str, dict[str, dict]] = TTLCache(
    maxsize=settings.PERMISSION_GROUPS_CACHE_SIZE,
    ttl=settings.PERMISSION_GROUPS_CACHE_TTL,
)


def _cache_key(authorization: str) -> str:
    return hashlib.sha256(authorization.encode()).hexdigest()


def clear_permission_groups_cache() -> None:
    _cache.clear()


async def get_own_permission_groups(authorization: str) -> dict[str, dict]:
    key = _cache_key(authorization)
    cached = _cache.get(key)
    if cached is not None:
        logger.debug("Using cached permission groups")
        return cached

    data = await fetch_dsm_api_or_raise(
        "/permission-group/", authorization, "fetching own permission groups"
    )
    permission_groups = {
        item["database_username"]: item
        for item in get_items(data)
        if item.get("database_username")
    }
    _cache[key] = permission_groups
    return permission_groups


async def fetch_own_permission_groups(authorization: str) -> dict[str, dict]:
    try:
        return await get_own_permission_groups(authorization)
    except HTTPException as e:
        logger.warning("Fetching own permission groups failed: %s", e.detail)
        return {}


def has_internal_access(endpoint_name: str, permission_groups: dict[str, dict]) -> bool:
    return endpoint_name in permission_groups
