import logging

import httpx
from fastapi import HTTPException

from services.dsm_api import fetch_dsm_api
from models.user import UserPublic

logger = logging.getLogger("app.services.user")


async def get_me_service(authorization: str | None) -> UserPublic:
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        return UserPublic.model_validate(await fetch_dsm_api("/me/", authorization))
    except httpx.TimeoutException:
        logger.warning("Timeout while fetching user info from DSM API")
        raise HTTPException(status_code=504, detail="DSM API timeout")
    except (httpx.HTTPError, ValueError) as e:
        logger.error("Fetching user info from DSM API failed: %s", e)
        raise HTTPException(status_code=502, detail="User info not available")
