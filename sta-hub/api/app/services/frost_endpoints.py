import logging

import httpx
from fastapi import HTTPException

from config import settings
from utils import normalize_search, remove_trailing_slash
from models import FrostEndpoint, FrostEndpointsResponse
from services.frost_proxy import public_frost
from services.ingests import fetch_ingest_permission_group_id
from services.permission_groups import (
    fetch_own_permission_groups,
    has_internal_access,
)

logger = logging.getLogger("app.services.frost_endpoints")


def rewrite_endpoint_url(url: str) -> str:
    """Point a URL from the FROST endpoint listing at the public base URL.

    FROST lists its endpoints with internal URLs (``settings.FROST_URL``).
    Clients must use the proxy instead, so the path is kept and put behind
    ``settings.BASE_URL``. Scheme and host of ``url`` are discarded.

    Args:
        url (str): An endpoint URL as listed by FROST.

    Returns:
        str: ``BASE_URL`` (without trailing slash) followed by the path.
    """
    path = httpx.URL(url).raw_path.decode()
    # strip possible path prefix of FROST_URL as proxy route adds it when forwarding
    frost_prefix = remove_trailing_slash(httpx.URL(settings.FROST_URL).path)
    if frost_prefix and path.startswith(frost_prefix + "/"):
        path = path[len(frost_prefix) :]
    return remove_trailing_slash(settings.BASE_URL) + path


def explicit_route_url(url: str, name: str, route: str) -> str:
    """Turn an endpoint URL of the automatic route into an explicit route URL.

    If endpoint name is not found as a path segment followed by ``/``, the url
    is returned unchanged.

    Args:
        url (str): The endpoint URL, e.g. ``http://host/sta/<name>/v1.1``.
        name (str): The FROST endpoint name.
        route (str): The explicit route, ``"public"`` or ``"internal"``.

    Returns:
        str: The URL with ``/<route>`` inserted before the endpoint name.

    Examples:
        >>> explicit_route_url("http://host/sta/proj/v1.1", "proj", "public")
        'http://host/sta/public/proj/v1.1'
    """
    return url.replace(f"/{name}/", f"/{route}/{name}/", 1)


def frost_display_name(group: str, project: str | None) -> str:
    """Build the name shown for an endpoint: the project, or else the group.

    Args:
        group (str): The endpoint's group name.
        project (str | None): The endpoint's project name, if any.

    Returns:
        str: ``project`` or ``group`` in upper case.

    Examples:
        >>> frost_display_name("ufz_group", "my_project")
        'MY_PROJECT'
        >>> frost_display_name("ufz_group", None)
        'UFZ_GROUP'
    """
    return (project or group).upper()


def endpoint_from_frost(raw: dict) -> FrostEndpoint:
    """Build a ``FrostEndpoint`` from an entry of the FROST endpoint listing.

    Besides mapping the fields, all URLs are pointed at the proxy: the
    automatic route (``url``) and the explicit ``/public`` and ``/internal``
    routes.

    Args:
        raw (dict): One entry of the listing's ``endpoints``.

    Returns:
        FrostEndpoint: The endpoint with proxy URLs.

    Raises:
        pydantic.ValidationError: If required fields (``name``, ``group``,
            ``url``) are missing or invalid.
    """
    group = raw.get("group")
    project = raw.get("project")
    endpoint = FrostEndpoint.model_validate(
        {
            "name": raw.get("name"),
            "display_name": frost_display_name(group or "", project),
            "group": group,
            "project": project,
            "url": raw.get("url"),
        }
    )
    endpoint.url = rewrite_endpoint_url(endpoint.url)
    endpoint.public_url = explicit_route_url(endpoint.url, endpoint.name, "public")
    endpoint.internal_url = explicit_route_url(endpoint.url, endpoint.name, "internal")
    return endpoint


def matches_query(endpoint: FrostEndpoint, q: str) -> bool:
    """Check whether an endpoint's display name contains the search query.

    Both sides are compared with ``normalize_search``.

    Args:
        endpoint (FrostEndpoint): The endpoint to check.
        q (str): The search query.

    Returns:
        bool: ``True`` if the normalized query is part of the normalized
        display name.
    """
    return normalize_search(q) in normalize_search(endpoint.display_name)


async def fetch_frost_endpoints() -> list[FrostEndpoint]:
    """Fetch the endpoint listing from the public FROST server.

    The listing is the source of all endpoints; the caller's permissions are
    applied afterwards. Redirects are followed.

    Returns:
        list[FrostEndpoint]: All listed endpoints with proxy URLs.

    Raises:
        HTTPException: 502 if FROST returns an error status or an invalid
            listing, 504 or 502 if FROST cannot be reached.
    """
    upstream = await public_frost.fetch(
        settings.FROST_ENDPOINTS_PATH,
        headers={"accept": "application/json"},
        follow_redirects=True,
    )
    try:
        upstream.raise_for_status()
        data = upstream.json()
        raw_endpoints = data.get("endpoints", []) if isinstance(data, dict) else []
        return [endpoint_from_frost(e) for e in raw_endpoints]
    except (httpx.HTTPStatusError, ValueError, AttributeError) as e:
        logger.error("Fetching FROST endpoints failed: %s", e)
        raise HTTPException(status_code=502, detail="FROST endpoints not available")


def mark_internal_endpoints(
    endpoints: list[FrostEndpoint], permission_groups: dict[str, dict]
) -> list[FrostEndpoint]:
    """Mark the endpoints the caller has access to and list them first.

    Args:
        endpoints (list[FrostEndpoint]): The endpoints to mark. They are
            modified in place.
        permission_groups (dict[str, dict]): The caller's permission groups.

    Returns:
        list[FrostEndpoint]: The endpoints, internal ones first.
    """
    for endpoint in endpoints:
        if has_internal_access(endpoint.name, permission_groups):
            endpoint.is_internal = True
    return sorted(endpoints, key=lambda e: not e.is_internal)


async def filter_by_ingest(
    endpoints: list[FrostEndpoint],
    permission_groups: dict[str, dict],
    authorization: str,
    ingest_id: int,
) -> list[FrostEndpoint]:
    """Keep only the endpoints belonging to the permission group of an ingest.

    Args:
        endpoints (list[FrostEndpoint]): The endpoints to filter.
        permission_groups (dict[str, dict]): The caller's permission groups.
        authorization (str): The caller's ``Authorization`` value.
        ingest_id (int): The DSM ingest id.

    Returns:
        list[FrostEndpoint]: The matching endpoints, or ``[]`` if the ingest
        does not exist, is not accessible or cannot be fetched.
    """
    permission_group_id = await fetch_ingest_permission_group_id(
        authorization, ingest_id
    )
    if permission_group_id is None:
        return []
    return [
        e
        for e in endpoints
        if permission_groups.get(e.name, {}).get("id") == permission_group_id
    ]


async def frost_endpoints_service(
    q: str | None = None,
    authorization: str | None = None,
    ingest_id: int | None = None,
) -> FrostEndpointsResponse:
    """List the FROST endpoints, personalized for the caller.

    Anonymous callers get all endpoints. Authenticated callers additionally
    get their accessible endpoints marked and listed first, and can restrict
    the result to the endpoints of one ingest.

    Args:
        q (str | None): Search query for the display name.
            Defaults to ``None``.
        authorization (str | None): The caller's ``Authorization`` value.
            Defaults to ``None``.
        ingest_id (int | None): Only return endpoints of this ingest. Ignored
            without ``authorization``. Defaults to ``None``.

    Returns:
        FrostEndpointsResponse: The resulting endpoints.

    Raises:
        HTTPException: 502 or 504 if the FROST listing is not available.
    """
    endpoints = await fetch_frost_endpoints()

    if authorization:
        permission_groups = await fetch_own_permission_groups(authorization)
        endpoints = mark_internal_endpoints(endpoints, permission_groups)
        if ingest_id is not None:
            endpoints = await filter_by_ingest(
                endpoints, permission_groups, authorization, ingest_id
            )

    if q:
        endpoints = [e for e in endpoints if matches_query(e, q)]

    logger.debug("Returning %s FROST endpoints", len(endpoints))
    return FrostEndpointsResponse(endpoints=endpoints)
