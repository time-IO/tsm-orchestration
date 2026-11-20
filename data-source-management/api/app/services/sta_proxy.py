import logging
from typing import Any

from fastapi import HTTPException
from httpx import AsyncClient, HTTPError

from access_scope import AccessScope
from config import settings

logger = logging.getLogger("app.services.sta_proxy")

STA_INTERNAL_ROUTE = "internal/"


def build_internal_sta_url(database_username: str, query: str) -> str:
    """Build the URL of a query against the internal STA endpoint of a project.

    Args:
        database_username (str): The project's database user.
        query (str): The STA query.

    Returns:
        str: ``<STA_ROOT_URL>/internal/<database_username><STA_VERSION><query>``.
    """
    root = settings.STA_ROOT_URL.rstrip("/") + "/"
    return root + STA_INTERNAL_ROUTE + database_username + settings.STA_VERSION + query


def get_database_username(
    permission_group_id: int, access_scope: AccessScope, repo_database
) -> str:
    """Return the database user of a permission group the caller may access.

    Args:
        permission_group_id (int): The permission group to query.
        access_scope (AccessScope): The caller's access scope.
        repo_database: Repository to look up the permission group's database.

    Returns:
        str: The database user, which is also the STA endpoint name.

    Raises:
        HTTPException: 422 without a permission group, 403 without access to
            it, 404 if it has no database.
    """
    if not permission_group_id:
        raise HTTPException(
            status_code=422, detail="No permission_group_id was provided"
        )

    if not access_scope.can_access_permission_group(permission_group_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied for current_user to this permission_group.",
        )

    database = repo_database.find_one_permission_group_id(permission_group_id)
    if not database:
        raise HTTPException(status_code=404, detail="Database not found.")
    return database.username


async def fetch_sta(url: str, token: str) -> Any:
    """Send a GET request to the STA with the caller's token.

    Args:
        url (str): The full STA URL.
        token (str): The caller's bearer token.

    Returns:
        Any: The decoded JSON response.

    Raises:
        HTTPException: The STA's status code if it returns an error, 502 if
            it is not reachable or returns invalid JSON.
    """
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with AsyncClient() as client:
            response = await client.get(url, headers=headers)
    except HTTPError as e:
        logger.error("STA request failed: %s", e)
        raise HTTPException(status_code=502, detail="STA not reachable")

    if response.is_error:
        logger.warning("STA request returned %s", response.status_code)
        raise HTTPException(
            status_code=response.status_code, detail="STA request failed"
        )

    try:
        return response.json()
    except ValueError as e:
        logger.error("Invalid STA response: %s", e)
        raise HTTPException(status_code=502, detail="Invalid STA response")


async def sta_proxy_service(
    permission_group_id: int,
    query: str,
    access_scope: AccessScope,
    repo_database,
    token: str,
) -> Any:
    """Run an STA query against the internal STA endpoint of a permission group.

    Args:
        permission_group_id (int): The permission group whose STA is queried.
        query (str): The STA query, e.g. ``Datastreams?$top=10``.
        access_scope (AccessScope): The caller's access scope.
        repo_database: Repository to look up the permission group's database.
        token (str): The caller's bearer token, forwarded to the STA.

    Returns:
        Any: The decoded JSON response of the STA.

    Raises:
        HTTPException: See ``get_database_username`` and ``fetch_sta``.
    """
    database_username = get_database_username(
        permission_group_id, access_scope, repo_database
    )
    return await fetch_sta(build_internal_sta_url(database_username, query), token)
