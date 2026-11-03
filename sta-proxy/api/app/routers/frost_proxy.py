import logging

from fastapi import APIRouter, Depends, Request, Response
from dependencies import get_authorization
from utils import validate_proxied_path
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
