import logging

import httpx

from config import settings

logger = logging.getLogger("app.services.permission_groups")


async def fetch_own_database_usernames(authorization: str) -> set[str]:
    """Fetch the current user's permission groups from the DSM API and
    return the set of associated FROST database usernames (schema names)."""
    try:
        async with httpx.AsyncClient(timeout=settings.FROST_TIMEOUT) as client:
            upstream = await client.get(
                f"{settings.DSM_API_URL}/permission-group/",
                headers={"authorization": authorization, "accept": "application/json"},
            )
        upstream.raise_for_status()
        data = upstream.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Fetching own permission groups failed: %s", e)
        return set()

    items = data.get("items", []) if isinstance(data, dict) else []
    return {
        item["database_username"] for item in items if item.get("database_username")
    }
