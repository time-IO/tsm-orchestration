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
    """Build an ``Ingest`` from a DSM API ingest item.

    Args:
        item (dict): An item of the DSM API ``/ingest/`` response.

    Returns:
        Ingest: The ingest with the permission group name if included.

    Raises:
        KeyError: If ``id``, ``uuid``, ``name`` or ``permission_group_id``
            is missing.
        pydantic.ValidationError: If a field has an invalid value.
    """
    permission_group = item.get("permission_group") or {}
    return Ingest(
        id=item["id"],
        uuid=item["uuid"],
        name=item["name"],
        permission_group_id=item["permission_group_id"],
        permission_group_name=permission_group.get("name"),
    )


def build_search_params(q: str) -> list[dict[str, str | int]]:
    """Build the DSM API queries for an ingest search.

    Args:
        q (str): The search query. Surrounding whitespace is ignored.

    Returns:
        list[dict[str, str | int]]: Query parameters for each request. An
        empty query yields a single unfiltered request.

    Examples:
        >>> build_search_params("")
        [{'size': 20}]
        >>> build_search_params("42")
        [{'id[eq]': 42}, {'name[ilike]': '%42%', 'size': 20}]
    """
    q = q.strip()
    if not q:
        return [{"size": SEARCH_LIMIT}]

    # search is a list since we need multiple requests to filter for the different properties.
    # DSM API does not offer disjunction search (combined with or) at the moment.
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
    """Search the caller's ingests by name, id or uuid.

    The DSM API applies the caller's permissions, so only accessible ingests
    are found.

    Args:
        authorization (str | None): The caller's ``Authorization`` value.
        q (str | None): The search query. Defaults to ``None`` (no filter).

    Returns:
        IngestsResponse: At most ``SEARCH_LIMIT`` ingests.

    Raises:
        HTTPException: 401 without valid credentials, 502 or 504 if the DSM
            API fails or returns invalid items.
    """
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
    """Run multiple ingest searches against the DSM API in parallel.

    Args:
        authorization (str): The caller's ``Authorization`` value.
        searches (list[dict[str, str | int]]): Query parameters per request,
            see ``build_search_params``.

    Returns:
        list: The decoded responses, in the order of ``searches``.

    Raises:
        HTTPException: 401, 502 or 504 if any request fails.
    """
    return await asyncio.gather(
        *(
            fetch_dsm_api_or_raise(
                "/ingest/", authorization, "searching ingests", params=params
            )
            for params in searches
        )
    )


def merge_ingests(results: list) -> list[Ingest]:
    """Combine ingest search results in order, dropping duplicates.

    Args:
        results (list): The decoded DSM API responses.

    Returns:
        list[Ingest]: The ingests, each id once, in order of first
        appearance.

    Raises:
        KeyError: If an item lacks a required field, see ``to_ingest``.
        pydantic.ValidationError: If an item has invalid values.
    """
    ingests: dict[int, Ingest] = {}
    for data in results:
        for item in get_items(data):
            if item["id"] not in ingests:
                ingests[item["id"]] = to_ingest(item)
    return list(ingests.values())


async def fetch_ingest_permission_group_id(
    authorization: str, ingest_id: int
) -> int | None:
    """Return the permission group id of one of the caller's ingests.

    Args:
        authorization (str): The caller's ``Authorization`` value.
        ingest_id (int): The DSM ingest id.

    Returns:
        int | None: The ``permission_group_id`` of the first matching item,
        or ``None`` if the ingest does not exist, is not accessible or the
        request fails.
    """
    try:
        data = await fetch_dsm_api(
            "/ingest/", authorization, params={"id[eq]": ingest_id}
        )
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Fetching ingest %s failed: %s", ingest_id, e)
        return None

    items = get_items(data)
    return items[0].get("permission_group_id") if items else None
