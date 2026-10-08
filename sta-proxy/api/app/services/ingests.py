import asyncio
import logging
from uuid import UUID

import httpx
from fastapi import HTTPException

from models import Ingest, IngestsResponse
from services.dsm_api import fetch_dsm_api

logger = logging.getLogger("app.services.ingests")

SEARCH_LIMIT = 20


def to_ingest(item: dict) -> Ingest:
    permission_group = item.get("permission_group") or {}
    return Ingest(
        id=item["id"],
        uuid=item["uuid"],
        name=item["name"],
        permission_group_id=item["permission_group_id"],
        permission_group_name=permission_group.get("name"),
    )


def build_search_params(q: str) -> list[dict[str, str | int]]:
    q = q.strip()
    if not q:
        return [{"size": SEARCH_LIMIT}]

    searches: list[dict[str, str | int]] = []
    # search is a list since we need multiple requests to filter for the different properties.
    # DSM API does not offer disjunction search (combined with or) at the moment.

    if q.isdigit():
        searches.append({"id[eq]": int(q)})
    try:
        searches.append({"uuid[eq]": str(UUID(q))})
    except ValueError:
        pass
    searches.append({"name[ilike]": f"%{q}%", "size": SEARCH_LIMIT})
    return searches


async def search_ingests_service(
    authorization: str | None, q: str | None = None
) -> IngestsResponse:
    """Search the user's ingests by name, id or uuid. Exact id/uuid
    matches come first."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        results = await asyncio.gather(
            *(
                fetch_dsm_api("/ingest/", authorization, params=params)
                for params in build_search_params(q or "")
            )
        )
    except httpx.TimeoutException:
        logger.warning("Timeout while searching ingests in DSM API")
        raise HTTPException(status_code=504, detail="DSM API timeout")
    except (httpx.HTTPError, ValueError) as e:
        logger.error("Searching ingests in DSM API failed: %s", e)
        raise HTTPException(status_code=502, detail="Ingests not available")

    ingests: dict[int, Ingest] = {}
    for data in results:
        for item in data.get("items", []) if isinstance(data, dict) else []:
            if item["id"] not in ingests:
                ingests[item["id"]] = to_ingest(item)

    return IngestsResponse(items=list(ingests.values())[:SEARCH_LIMIT])


async def fetch_ingest_permission_group_id(
    authorization: str, ingest_id: int
) -> int | None:
    """Return the permission group id of one of the user's ingests,
    or None if the ingest does not exist or is not accessible."""
    try:
        data = await fetch_dsm_api(
            "/ingest/", authorization, params={"id[eq]": ingest_id}
        )
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Fetching ingest %s failed: %s", ingest_id, e)
        return None

    items = data.get("items", []) if isinstance(data, dict) else []
    return items[0]["permission_group_id"] if items else None
