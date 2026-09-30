import logging

from fastapi import APIRouter, Header
from models import IngestsResponse
from services.ingests import search_ingests_service

logger = logging.getLogger("app.routers.ingests")

router = APIRouter(
    prefix="/ingests",
    tags=["ingests"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "",
    summary="Searches the current user's ingests by name, id or uuid, proxied from the DSM API",
)
@router.get("/", include_in_schema=False)
async def search_ingests(
    q: str | None = None,
    authorization: str | None = Header(default=None),
) -> IngestsResponse:
    return await search_ingests_service(authorization, q)
