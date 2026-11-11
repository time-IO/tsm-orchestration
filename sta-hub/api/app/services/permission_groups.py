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
    """Derive the cache key from the credentials without storing them in plain text.

    Args:
        authorization (str): The caller's ``Authorization`` value.

    Returns:
        str: The SHA-256 hex digest of ``authorization``.
    """
    return hashlib.sha256(authorization.encode()).hexdigest()


def clear_permission_groups_cache() -> None:
    """Remove all cached permission groups."""
    _cache.clear()


async def get_own_permission_groups(authorization: str) -> dict[str, dict]:
    """Return the caller's permission groups, cached per credentials.

    The access check runs on every proxied request, so the DSM API lookup is
    cached for ``settings.PERMISSION_GROUPS_CACHE_TTL`` seconds per
    ``Authorization`` value. Failed lookups are not cached.

    Note: Permission changes in the DSM therefore take
    effect after at most that time.

    Args:
        authorization (str): The caller's ``Authorization`` value.

    Returns:
        dict[str, dict]: The permission groups keyed by their
        ``database_username``, which equals the FROST endpoint name.

    Raises:
        HTTPException: 401 if the DSM API rejects the credentials, 504 on a
            timeout, 502 on other DSM API errors.
    """
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
    """Return the caller's permission groups, or none if the lookup fails.

    For features where a DSM API problem should not fail the whole request.

    Args:
        authorization (str): The caller's ``Authorization`` value.

    Returns:
        dict[str, dict]: The permission groups as returned by
        ``get_own_permission_groups``, or ``{}`` if the lookup failed.
    """
    try:
        return await get_own_permission_groups(authorization)
    except HTTPException as e:
        logger.warning("Fetching own permission groups failed: %s", e.detail)
        return {}


def has_internal_access(endpoint_name: str, permission_groups: dict[str, dict]) -> bool:
    """Check whether the permission groups grant access to an endpoint.

    The name must match a permission group's ``database_username`` exactly.

    Args:
        endpoint_name (str): The FROST endpoint name.
        permission_groups (dict[str, dict]): The caller's permission groups,
            see ``get_own_permission_groups``.

    Returns:
        bool: ``True`` if a permission group with that name exists.

    Examples:
        >>> has_internal_access("my_project", {"my_project": {"id": 1}})
        True
        >>> has_internal_access("my_projectx", {"my_project": {"id": 1}})
        False
    """
    return endpoint_name in permission_groups
