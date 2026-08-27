from fastapi import APIRouter, Depends, HTTPException
import httpx
from access_scope import AccessScope
from config import settings
from dependencies import get_current_user, get_repo_database
from models import User

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
    current_user: User = Depends(get_current_user),
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
    username = database.username

    async with httpx.AsyncClient() as client:
        response = await client.get(
            settings.STA_ROOT_URL + username + settings.STA_VERSION + q
        )
    try:
        return response.json()
    except Exception as e:
        print(f"Error during sta request:: {str(e)}")
        raise HTTPException(status_code=404, detail="Not Found")
