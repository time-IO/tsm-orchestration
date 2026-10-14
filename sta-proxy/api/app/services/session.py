import logging

import httpx
from fastapi import HTTPException, Response

from config import settings
from services.dsm_api import fetch_dsm_api

logger = logging.getLogger("app.services.session")

# browser's max cookie size is 4KB
MAX_COOKIE_VALUE_SIZE = 3500


def get_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def check_origin(origin: str | None) -> None:
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
    # cookie Secure attribute depends on the protocol (defined with BASE_URL)
    return httpx.URL(settings.BASE_URL).scheme == "https"


async def validate_token(authorization: str) -> None:
    try:
        await fetch_dsm_api("/me/", authorization)
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            raise HTTPException(status_code=401, detail="Not authenticated")
        logger.error("Validating token with DSM API failed: %s", e)
        raise HTTPException(status_code=502, detail="DSM API not available")
    except httpx.TimeoutException:
        logger.warning("Timeout while validating token with DSM API")
        raise HTTPException(status_code=504, detail="DSM API timeout")
    except httpx.HTTPError as e:
        logger.error("Validating token with DSM API failed: %s", e)
        raise HTTPException(status_code=502, detail="DSM API not available")


async def set_session_service(
    response: Response, authorization: str | None, origin: str | None
) -> None:
    check_origin(origin)
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
    check_origin(origin)
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path=settings.SESSION_COOKIE_PATH,
        secure=is_cookie_secure(),
        httponly=True,
        samesite="lax",
    )
