import logging

from fastapi import APIRouter, Header, Response
from services.session import clear_session_service, set_session_service

logger = logging.getLogger("app.routers.session")

router = APIRouter(
    prefix="/session",
    tags=["session"],
)


@router.put(
    "",
    status_code=204,
    summary="Stores the access token in an HttpOnly cookie",
)
@router.put("/", status_code=204, include_in_schema=False)
async def set_session(
    response: Response,
    authorization: str | None = Header(default=None),
    origin: str | None = Header(default=None),
) -> None:
    await set_session_service(response, authorization, origin)


@router.delete("", status_code=204, summary="Removes the session cookie")
@router.delete("/", status_code=204, include_in_schema=False)
async def clear_session(
    response: Response, origin: str | None = Header(default=None)
) -> None:
    clear_session_service(response, origin)
