import logging

from fastapi import APIRouter
from models import FrostEndpointsResponse
from services import frost_endpoints_service

logger = logging.getLogger("app.routers.frost_endpoints")

router = APIRouter(
    prefix="/endpoints",
    tags=["endpoints"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "",
    summary="Returns the list of FROST endpoints with public urls",
)
@router.get("/", include_in_schema=False)
async def list_endpoints(q: str | None = None) -> FrostEndpointsResponse:
    return await frost_endpoints_service(q=q)
