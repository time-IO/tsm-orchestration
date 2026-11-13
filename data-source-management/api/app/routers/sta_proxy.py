import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import AsyncClient, HTTPError
from access_scope import AccessScope
from config import settings
from dependencies import bearer_scheme, get_current_user, get_repo_database
from models import User

logger = logging.getLogger("app.routers.sta_proxy")

STA_INTERNAL_ROUTE = "internal/"

router = APIRouter(
    prefix="/sta",
    tags=["sta"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)


def build_internal_sta_url(database_username: str, query: str) -> str:
    """Build the URL of a query against the internal STA endpoint of a project.

    Args:
        database_username (str): The project's database user.
        query (str): The STA query.

    Returns:
        str: ``<STA_ROOT_URL>/internal/<database_username><STA_VERSION><query>``.
    """
    root = settings.STA_ROOT_URL.rstrip("/") + "/"
    return root + STA_INTERNAL_ROUTE + database_username + settings.STA_VERSION + query


@router.get("/")
async def redirect_query(
    permission_group_id: int,
    q: str,
    repo=Depends(get_repo_database),
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):

    if not permission_group_id:
        raise HTTPException(
            status_code=422, detail="No permission_group_id was provided"
        )

    if not AccessScope.from_user(current_user).can_access_permission_group(
        permission_group_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied for current_user to this permission_group.",
        )

    database = repo.find_one_permission_group_id(permission_group_id)

    if not database:
        raise HTTPException(status_code=404, detail="Database not found.")

    # requests without a token are rejected already
    headers = {"Authorization": f"Bearer {credentials.credentials}"}
    url = build_internal_sta_url(database.username, q)

    try:
        async with AsyncClient() as client:
            response = await client.get(url, headers=headers)
    except HTTPError as e:
        logger.error("STA request failed: %s", e)
        raise HTTPException(status_code=502, detail="STA not reachable")

    if response.is_error:
        logger.warning("STA request returned %s", response.status_code)
        raise HTTPException(
            status_code=response.status_code, detail="STA request failed"
        )

    try:
        return response.json()
    except ValueError as e:
        logger.error("Invalid STA response: %s", e)
        raise HTTPException(status_code=502, detail="Invalid STA response")
