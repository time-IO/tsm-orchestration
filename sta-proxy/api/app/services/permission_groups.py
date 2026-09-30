import logging

import httpx

from services.dsm_api import fetch_dsm_api

logger = logging.getLogger("app.services.permission_groups")


async def fetch_own_permission_groups(authorization: str) -> dict[str, dict]:
    try:
        data = await fetch_dsm_api("/permission-group/", authorization)
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Fetching own permission groups failed: %s", e)
        return {}

    items = data.get("items", []) if isinstance(data, dict) else []
    return {
        item["database_username"]: item
        for item in items
        if item.get("database_username")
    }
