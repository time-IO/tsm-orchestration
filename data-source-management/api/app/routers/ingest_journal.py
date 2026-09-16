import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from access_scope import AccessScope
from config import settings
from dependencies import get_current_user, get_repo_ingest
from models import User

logger = logging.getLogger("app.ingest_journal")

router = APIRouter(
    prefix="/ingest",
    tags=["ingest/journal"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)


@router.get("/{ingest_id}/journal")
async def get_ingest_journal(
    ingest_id: int,
    datetime_from: Optional[str] = Query(None),
    datetime_to: Optional[str] = Query(None),
    level: Optional[str] = Query(
        None, description="Filter by level, e.g. INFO/WARNING/ERROR"
    ),
    limit: int = Query(100, description="Max entries, newest first"),
    repo=Depends(get_repo_ingest),
    current_user: User = Depends(get_current_user),
):
    """Return journal entries for an ingest.

    Resolves the ingest (enforcing the caller's permission-group access) and
    proxies the request to the timeio-db-api journal endpoint, keeping the
    db-api bearer token server-side.
    """
    # Raises 404 if the ingest does not exist or the user may not access it.
    ingest = repo.find_one(ingest_id, access_scope=AccessScope.from_user(current_user))

    if not settings.DB_API_BASE_URL:
        raise HTTPException(status_code=503, detail="DB API is not configured")

    params: dict = {"limit": limit}
    if datetime_from:
        params["datetime_from"] = datetime_from
    if datetime_to:
        params["datetime_to"] = datetime_to
    if level:
        params["level"] = level

    url = f"{settings.DB_API_BASE_URL}/things/{ingest.uuid}/journal"
    headers = {"Authorization": f"Bearer {settings.DB_API_AUTH_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.warning(
            "DB API returned %s for journal of ingest %s",
            e.response.status_code,
            ingest_id,
        )
        raise HTTPException(
            status_code=502, detail="Failed to fetch journal entries from DB API"
        )
    except httpx.HTTPError as e:
        logger.warning("Failed to reach DB API for journal: %s", e)
        raise HTTPException(status_code=502, detail="Failed to reach DB API")
