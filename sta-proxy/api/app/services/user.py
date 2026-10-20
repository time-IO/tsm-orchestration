import logging

import httpx
from fastapi import HTTPException

from services.dsm_api import dsm_error_to_http_exception, fetch_dsm_api
from models.user import UserPublic

logger = logging.getLogger("app.services.user")


async def get_me_service(authorization: str | None) -> UserPublic:
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        return UserPublic.model_validate(await fetch_dsm_api("/me/", authorization))
    except httpx.HTTPError as e:
        raise dsm_error_to_http_exception(e, "fetching user info")
    except ValueError as e:
        logger.error("DSM API returned invalid user info: %s", e)
        raise HTTPException(status_code=502, detail="User info not available")
