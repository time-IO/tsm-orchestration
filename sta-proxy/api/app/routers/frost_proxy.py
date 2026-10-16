import logging

from fastapi import APIRouter, HTTPException, Request, Response
from config import settings
from services import frost_proxy_service

logger = logging.getLogger("app.routers.frost_proxy")

router = APIRouter(
    tags=["frost"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{endpoint:path}",
    summary="Forwards GET /<endpoint>?<query> to the FROST server",
)
async def proxy_to_frost(endpoint: str, request: Request) -> Response:
    validate_proxied_path(endpoint)

    logger.debug("Proxy request for endpoint=%s query=%s", endpoint, request.url.query)
    return await frost_proxy_service(
        endpoint=endpoint,
        query=request.url.query,
        accept=request.headers.get("accept"),
    )


def validate_proxied_path(endpoint: str) -> None:
    # reject path traversal
    if ".." in endpoint.split("/"):
        raise HTTPException(status_code=400, detail="Invalid path")

    # hide FROST endpoint listing
    if endpoint.strip("/") == settings.FROST_ENDPOINTS_PATH.strip("/"):
        raise HTTPException(status_code=404, detail="Not Found")
