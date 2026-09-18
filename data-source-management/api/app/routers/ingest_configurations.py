import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from access_scope import AccessScope
from config import settings
from dependencies import get_current_user, get_repo_ingest
from models import User

logger = logging.getLogger("app.ingest_configurations")

router = APIRouter(
    prefix="/ingest",
    tags=["ingest/configurations"],
    responses={404: {"description": "Not foundasd"}},
    dependencies=[Depends(get_current_user)],
)


@router.get("/{ingest_id}/configurations")
async def get_ingest_configurations(
    ingest_id: int,
    repo=Depends(get_repo_ingest),
    current_user: User = Depends(get_current_user),
):
    """Return configurations entries for an ingest.

    Resolves the ingest (enforcing the caller's permission-group access) and
    proxies the request to the timeio-db-api configurations endpoint, keeping the
    db-api bearer token server-side.
    """
    # Raises 404 if the ingest does not exist or the user may not access it.
    ingest = repo.find_one(ingest_id, access_scope=AccessScope.from_user(current_user))

    if not settings.DB_API_BASE_URL:
        raise HTTPException(status_code=503, detail="DB API is not configured")

    url = f"{settings.DB_API_BASE_URL}/things/{ingest.uuid}/configurations"
    headers = {"Authorization": f"Bearer {settings.DB_API_AUTH_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as e:
        logger.warning(
            "DB API returned %s for configurations of ingest %s",
            e.response.status_code,
            ingest_id,
        )
        raise HTTPException(
            status_code=502, detail="Failed to fetch configurations"
        ) from e
    except httpx.HTTPError as e:
        logger.warning("Failed to reach DB API for configurations: %s", e)
        raise HTTPException(status_code=502, detail="Failed to reach DB API") from e

    sms_root = settings.SMS_ROOT_URL.rstrip("/")
    entries_with_url = [
        {
            "id": entry["id"],
            "label": entry["label"],
            "url": f"{sms_root}/configurations/{entry['id']}",
        }
        for entry in data
    ]

    return entries_with_url
