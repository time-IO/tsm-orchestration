import asyncio
import logging
from uuid import UUID

import httpx

from models import Ingest, IngestsResponse
from services.dsm_api import (
    dsm_error_to_http_exception,
    fetch_dsm_api,
    fetch_dsm_api_or_raise,
    get_items,
    require_authorization,
)

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

    # DSM API has no OR filter: one request per searched property
    searches: list[dict[str, str | int]] = []
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
    """Search the user's ingests by name, id or uuid. All run async."""
    authorization = require_authorization(authorization)
    results = await run_ingest_searches(authorization, build_search_params(q or ""))
    try:
        ingests = merge_ingests(results)
    except (KeyError, ValueError) as e:
        raise dsm_error_to_http_exception(e, "searching ingests")
    return IngestsResponse(items=ingests[:SEARCH_LIMIT])


async def run_ingest_searches(
    authorization: str, searches: list[dict[str, str | int]]
) -> list:
    """Run all searches against the DSM API in parallel."""
    return await asyncio.gather(
        *(
            fetch_dsm_api_or_raise(
                "/ingest/", authorization, "searching ingests", params=params
            )
            for params in searches
        )
    )


def merge_ingests(results: list) -> list[Ingest]:
    """Combine the search results in order, dropping duplicates."""
    ingests: dict[int, Ingest] = {}
    for data in results:
        for item in get_items(data):
            if item["id"] not in ingests:
                ingests[item["id"]] = to_ingest(item)
    return list(ingests.values())


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

    items = get_items(data)
    return items[0].get("permission_group_id") if items else None
