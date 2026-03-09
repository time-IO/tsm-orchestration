from fastapi import APIRouter, Depends, HTTPException
import httpx
from sentry_sdk.utils import current_stacktrace

from config import settings
from dependencies import get_current_user, get_repo_database

router = APIRouter(
    prefix="/sta",
    tags=["sta"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)


@router.get("/")
async def redirect_query(
    permission_group_id: int,
    q: str,
    repo=Depends(get_repo_database),
    current_user=Depends(get_current_user),
):

    if not permission_group_id:
        raise HTTPException(
            status_code=422, detail="No permission_group_id was provided"
        )

    if permission_group_id not in current_user.permission_group_ids:
        raise HTTPException(
            status_code=403,
            detail="Access denied for current_user to this permission_group.",
        )

    database = repo.find_one_permission_group_id(permission_group_id)

    if not database:
        raise HTTPException(status_code=404, detail="Database not found.")
    username = database.username

    async with httpx.AsyncClient() as client:
        response = await client.get(
            settings.STA_ROOT_URL + username + settings.STA_VERSION + q
        )
    try:
        return response.json()
    except httpx.DecodingError:
        raise HTTPException(status_code=502, detail="Invalid JSON in response")
