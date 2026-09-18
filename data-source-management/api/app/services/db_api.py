import logging
from typing import Any, Optional
from uuid import UUID

import httpx
from fastapi import HTTPException

from config import settings

logger = logging.getLogger("app.services.db_api")


def _build_query_params(**params: Any) -> dict:
    return {key: value for key, value in params.items() if value is not None}


async def _fetch_db_api(path: str, *, params: dict | None = None) -> Any:
    """fetches the timeio-db-api, keeping the bearer token server-side.

    Raises HTTPException if the db-api is not configured, is unreachable or returns an error.
    """
    if not settings.DB_API_BASE_URL:
        raise HTTPException(status_code=503, detail="DB API is not configured")

    url = f"{settings.DB_API_BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {settings.DB_API_AUTH_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.warning(f"DB API returned {e.response.status_code} for {path}")
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch DB API"
        ) from e
    except httpx.HTTPError as e:
        logger.warning(f"Failed to reach DB API for {path}: {e}")
        raise HTTPException(status_code=502, detail="Failed to reach DB API") from e


async def get_ingest_configurations(ingest_uuid: UUID) -> list[dict]:
    data = await _fetch_db_api(
        f"/things/{ingest_uuid}/configurations",
    )

    sms_root = settings.SMS_ROOT_URL.rstrip("/")
    return [
        {
            "id": entry["id"],
            "label": entry["label"],
            "url": f"{sms_root}/configurations/{entry['id']}",
        }
        for entry in data
    ]


async def get_ingest_journal(
    ingest_uuid: UUID,
    datetime_from: Optional[str] = None,
    datetime_to: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
) -> dict:
    params = _build_query_params(
        limit=limit,
        datetime_from=datetime_from,
        datetime_to=datetime_to,
        level=level,
    )
    return await _fetch_db_api(
        f"/things/{ingest_uuid}/journal",
        params=params,
    )
