import logging

from fastapi import APIRouter, Depends, Header, Request, Response, HTTPException
from config import settings
from services import frost_proxy_service

logger = logging.getLogger("app.routers.frost_proxy")

router = APIRouter(
    tags=["frost"],
    responses={404: {"description": "Not found"}},
)


def get_authorization(
    request: Request,
    authorization: str | None = Header(default=None),
) -> str | None:
    # opening an endpoint URL cannot send the bearer token,
    # instead it uses the session cookie
    if not authorization:
        token = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if token:
            authorization = f"Bearer {token}"
    return authorization


@router.get(
    "/{endpoint:path}",
    summary="Forwards GET /<endpoint>?<query> to the respective FROST server",
)
async def proxy_to_frost(
    endpoint: str,
    request: Request,
    authorization: str | None = Depends(get_authorization),
) -> Response:
    validate_proxied_path(endpoint)

    logger.debug("Proxy request for endpoint=%s query=%s", endpoint, request.url.query)
    return await frost_proxy_service(
        endpoint=endpoint,
        query=request.url.query,
        accept=request.headers.get("accept"),
        authorization=authorization,
    )


def validate_proxied_path(endpoint: str) -> None:
    # reject path traversal
    if ".." in endpoint.split("/"):
        raise HTTPException(status_code=400, detail="Invalid path")

    # hide FROST endpoint listing
    if endpoint.strip("/") == settings.FROST_ENDPOINTS_PATH.strip("/"):
        raise HTTPException(status_code=404, detail="Not Found")
