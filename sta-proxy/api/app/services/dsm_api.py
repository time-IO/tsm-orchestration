import logging
from typing import Any

import httpx
from fastapi import HTTPException

from config import settings
from utils import remove_trailing_slash

logger = logging.getLogger("app.services.dsm_api")

_client: httpx.AsyncClient | None = None


def get_dsm_client() -> httpx.AsyncClient:
    """Return the shared DSM API client, creating it if missing or closed.

    Returns:
        httpx.AsyncClient: A client bound to ``settings.DSM_API_URL``.
    """
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=remove_trailing_slash(settings.DSM_API_URL),
            timeout=settings.DSM_API_TIMEOUT,
        )
    return _client


async def close_dsm_client() -> None:
    """Close the DSM API client, if one was created. Recommended on application shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def fetch_dsm_api(
    path: str,
    authorization: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Send a GET request to the DSM API on behalf of the caller.

    The caller's credentials are forwarded, so the DSM API applies the
    caller's own permissions.

    Args:
        path (str): Path relative to ``settings.DSM_API_URL``.
        authorization (str): The caller's ``Authorization`` value.
        params (dict[str, Any] | None): Query parameters.
            Defaults to ``None``.

    Returns:
        Any: The decoded JSON body.

    Raises:
        httpx.HTTPStatusError: If the DSM API responds with an error status.
        httpx.HTTPError: On timeouts or connection errors.
        ValueError: If the body is not valid JSON.
    """
    response = await get_dsm_client().get(
        path,
        headers={"authorization": authorization, "accept": "application/json"},
        params=params,
    )
    logger.debug("DSM API responded with %s for %s", response.status_code, path)
    response.raise_for_status()
    return response.json()


def dsm_error_to_http_exception(e: Exception, action: str) -> HTTPException:
    """Translate a DSM API error into the error returned to the caller.

    DSM API internals are not exposed: rejected credentials become 401,
    everything else a generic gateway error.

    Args:
        e (Exception): The error raised while talking to the DSM API.
        action (str): What was attempted, used in log messages, e.g.
            ``"fetching user info"``.

    Returns:
        HTTPException: 401 if the DSM API answered 401 or 403, 504 on a
        timeout, 502 for anything else (including other error statuses and
        invalid responses).
    """
    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code in (401, 403):
        return HTTPException(status_code=401, detail="Not authenticated")
    if isinstance(e, httpx.TimeoutException):
        logger.warning("Timeout while %s with DSM API", action)
        return HTTPException(status_code=504, detail="DSM API timeout")
    logger.error("%s with DSM API failed: %s", action.capitalize(), e)
    return HTTPException(status_code=502, detail="DSM API not available")


def require_authorization(authorization: str | None) -> str:
    """Ensure credentials are present before calling the DSM API.

    Args:
        authorization (str | None): The caller's ``Authorization`` value.

    Returns:
        str: ``authorization``, narrowed to ``str``.

    Raises:
        HTTPException: 401 if ``authorization`` is missing or empty.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return authorization


async def fetch_dsm_api_or_raise(
    path: str,
    authorization: str,
    action: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Call ``fetch_dsm_api`` and raise its errors as ``HTTPException``.

    Args:
        path (str): Path relative to ``settings.DSM_API_URL``.
        authorization (str): The caller's ``Authorization`` value.
        action (str): What is attempted, used in log messages.
        params (dict[str, Any] | None): Query parameters.
            Defaults to ``None``.

    Returns:
        Any: The decoded JSON body.

    Raises:
        HTTPException: 401, 502 or 504, see ``dsm_error_to_http_exception``.
    """
    try:
        return await fetch_dsm_api(path, authorization, params)
    except (httpx.HTTPError, ValueError) as e:
        raise dsm_error_to_http_exception(e, action)


def get_items(data: Any) -> list[dict]:
    """Return the dict items of a paginated DSM API response.

    Tolerates unexpected response shapes instead of failing, so callers can
    iterate the result without further checks.

    Args:
        data (Any): The decoded JSON body.

    Returns:
        list[dict]: The dict entries of ``data["items"]``, or ``[]`` if
        ``data`` has no ``items`` list.

    Examples:
        >>> get_items({"items": [{"id": 1}, "invalid"]})
        [{'id': 1}]
        >>> get_items(None)
        []
    """
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]
