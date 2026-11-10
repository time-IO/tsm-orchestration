import logging

from fastapi import APIRouter, Header
from models import UserPublic
from services.user import get_me_service

logger = logging.getLogger("app.routers.user")

router = APIRouter(
    prefix="/me",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "",
    summary="Returns info about the currently authenticated user, proxied from the DSM API",
)
@router.get("/", include_in_schema=False)
async def get_me(authorization: str | None = Header(default=None)) -> UserPublic:
    return await get_me_service(authorization)
