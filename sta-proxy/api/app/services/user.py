import logging

import httpx
from fastapi import HTTPException

from config import settings
from models import UserPublic

logger = logging.getLogger("app.services.user")


async def get_me_service(authorization: str | None) -> UserPublic:
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        async with httpx.AsyncClient(timeout=settings.FROST_TIMEOUT) as client:
            upstream = await client.get(
                f"{settings.DSM_API_URL}/me/",
                headers={"authorization": authorization, "accept": "application/json"},
            )
        upstream.raise_for_status()
        return UserPublic.model_validate(upstream.json())
    except httpx.TimeoutException:
        logger.warning("Timeout while fetching user info from DSM API")
        raise HTTPException(status_code=504, detail="DSM API timeout")
    except (httpx.HTTPError, ValueError) as e:
        logger.error("Fetching user info from DSM API failed: %s", e)
        raise HTTPException(status_code=502, detail="User info not available")
