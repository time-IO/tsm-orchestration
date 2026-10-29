import logging

from fastapi import APIRouter, Depends, Header, Request, Response, HTTPException
from config import settings
from services import (
    frost_proxy_service,
    internal_frost_proxy_service,
    public_frost_proxy_service,
)

logger = logging.getLogger("app.routers.frost_proxy")

router = APIRouter(
    tags=["frost"],
    responses={404: {"description": "Not found"}},
)


def get_authorization(
    request: Request,
    authorization: str | None = Header(default=None),
) -> str | None:
    # browser navigation cannot send a bearer token; fall back to the session cookie
    if not authorization:
        token = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if token:
            authorization = f"Bearer {token}"
    return authorization


@router.get(
    "/public/{endpoint:path}",
    summary="Forwards GET /public/<endpoint>?<query> directly to the public FROST server",
)
async def proxy_to_public_frost(endpoint: str, request: Request) -> Response:
    validate_proxied_path(endpoint)
    logger.debug(
        "Public proxy request for endpoint=%s query=%s", endpoint, request.url.query
    )
    return await public_frost_proxy_service(
        endpoint=endpoint,
        query=request.url.query,
        accept=request.headers.get("accept"),
    )


@router.get(
    "/internal/{endpoint:path}",
    summary="Forwards GET /internal/<endpoint>?<query> directly to the internal FROST server",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "No access to internal endpoint"},
    },
)
async def proxy_to_internal_frost(
    endpoint: str,
    request: Request,
    authorization: str | None = Depends(get_authorization),
) -> Response:
    validate_proxied_path(endpoint)
    logger.debug(
        "Internal proxy request for endpoint=%s query=%s", endpoint, request.url.query
    )
    return await internal_frost_proxy_service(
        endpoint=endpoint,
        query=request.url.query,
        accept=request.headers.get("accept"),
        authorization=authorization,
    )


@router.get(
    "/{endpoint:path}",
    summary="Forwards GET /<endpoint>?<query> to the respective FROST server based on authentication status",
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


AMBIGUOUS_PATH_CHARS = (";", "%", "\\")


def validate_proxied_path(endpoint: str) -> None:
    # reject path traversal
    segments = endpoint.split("/")
    if any(s in (".", "..") for s in segments) or any(
        c in endpoint for c in AMBIGUOUS_PATH_CHARS
    ):
        raise HTTPException(status_code=400, detail="Invalid path")

    # hide FROST endpoint listing
    if endpoint.strip("/") == settings.FROST_ENDPOINTS_PATH.strip("/"):
        raise HTTPException(status_code=404, detail="Not Found")
