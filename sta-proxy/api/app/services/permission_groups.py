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


async def search_own_ingests(authorization: str, ingest_query: str) -> set[str]:
    """Search the user's own ingests by name and return the set of
    FROST database usernames belonging to the matching ingests'
    permission groups."""
    try:
        async with httpx.AsyncClient(timeout=settings.FROST_TIMEOUT) as client:
            ingest_response = await client.get(
                f"{settings.DSM_API_URL}/ingest/",
                headers={"authorization": authorization, "accept": "application/json"},
                params={"name[ilike]": f"%{ingest_query}%"},
            )
            ingest_response.raise_for_status()
            ingest_data = ingest_response.json()

            pg_response = await client.get(
                f"{settings.DSM_API_URL}/permission-group/",
                headers={"authorization": authorization, "accept": "application/json"},
            )
            pg_response.raise_for_status()
            pg_data = pg_response.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Searching own ingests failed: %s", e)
        return set()

    matching_group_ids = {
        item["permission_group_id"] for item in ingest_data.get("items", [])
    }

    return {
        pg["database_username"]
        for pg in pg_data.get("items", [])
        if pg["id"] in matching_group_ids and pg.get("database_username")
    }
