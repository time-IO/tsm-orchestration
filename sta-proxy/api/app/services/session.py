import logging

import httpx
from fastapi import HTTPException, Response

from config import settings
from services.dsm_api import fetch_dsm_api_or_raise, require_authorization

logger = logging.getLogger("app.services.session")

# browser's max cookie size is 4KB
MAX_COOKIE_VALUE_SIZE = 3500


def get_bearer_token(authorization: str | None) -> str | None:
    """Extract the token from a bearer ``Authorization`` value.

    Args:
        authorization (str | None): The ``Authorization`` header.

    Returns:
        str | None: The token without surrounding whitespace, or ``None`` if
        the value is missing, uses another scheme or has no token.

    Examples:
        >>> get_bearer_token("Bearer abc")
        'abc'
    """
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def check_origin(origin: str | None) -> None:
    """Ensure session requests come from the frontend (CSRF protection).

    Browsers send an ``Origin`` header with cross-site requests, so other
    sites cannot set or clear the session cookie. Requests without
    ``Origin`` (e.g. non-browser clients) are accepted.

    Args:
        origin (str | None): The ``Origin`` header.

    Raises:
        HTTPException: 403 if scheme, host or port differ from
            ``settings.BASE_URL``.
    """
    if origin is None:
        return
    allowed = httpx.URL(settings.BASE_URL)  # only frontend may manage sessions
    actual = httpx.URL(origin)
    if (actual.scheme, actual.host, actual.port) != (
        allowed.scheme,
        allowed.host,
        allowed.port,
    ):
        logger.warning("Rejected session request from origin %s", origin)
        raise HTTPException(status_code=403, detail="Origin not allowed")


def is_cookie_secure() -> bool:
    """Check whether the session cookie must be marked ``Secure``.

    Returns:
        bool: ``True`` if ``settings.BASE_URL`` uses HTTPS.
    """
    # cookie Secure attribute depends on the protocol (defined with BASE_URL)
    return httpx.URL(settings.BASE_URL).scheme == "https"


async def validate_token(authorization: str) -> None:
    """Ensure the DSM API accepts the credentials by requesting ``/me/``.

    Args:
        authorization (str): The caller's ``Authorization`` value.

    Raises:
        HTTPException: 401 if the credentials are rejected, 502 or 504 if
            the DSM API fails.
    """
    await fetch_dsm_api_or_raise("/me/", authorization, "validating token")


async def set_session_service(
    response: Response, authorization: str | None, origin: str | None
) -> None:
    """Store the caller's bearer token in an HTTP-only session cookie.

    Lets browser navigation (e.g. opening FROST links) use the caller's
    permissions, see ``dependencies.get_authorization``. The token is
    validated against the DSM API before it is stored.

    Args:
        response (Response): The response to set the cookie on.
        authorization (str | None): The caller's ``Authorization`` header.
        origin (str | None): The ``Origin`` header.

    Raises:
        HTTPException: 403 for a foreign origin, 401 without a valid bearer
            token, 413 if the token is too large for a cookie, 502 or 504 if
            the DSM API fails.
    """
    check_origin(origin)
    authorization = require_authorization(authorization)
    token = get_bearer_token(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await validate_token(authorization)

    if len(token) > MAX_COOKIE_VALUE_SIZE:
        logger.warning(
            "Access token (%s bytes) too large for a cookie",
            len(token),
        )
        raise HTTPException(status_code=413, detail="Access token too large")

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        path=settings.SESSION_COOKIE_PATH,
        secure=is_cookie_secure(),
        httponly=True,
        samesite="lax",
    )


def clear_session_service(response: Response, origin: str | None) -> None:
    """Delete the session cookie (logout).

    The cookie attributes must match those used when setting it, otherwise
    browsers keep the cookie.

    Args:
        response (Response): The response to delete the cookie on.
        origin (str | None): The ``Origin`` header.

    Raises:
        HTTPException: 403 for a foreign origin.
    """
    check_origin(origin)
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path=settings.SESSION_COOKIE_PATH,
        secure=is_cookie_secure(),
        httponly=True,
        samesite="lax",
    )
