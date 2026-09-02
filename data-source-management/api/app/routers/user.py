from fastapi import APIRouter, Depends
from dependencies import get_current_user, sync_permission_groups
from models.user import UserPublic

router = APIRouter(
    prefix="/me",
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user), Depends(sync_permission_groups)],
)


@router.get("/", response_model=UserPublic)
def read_user(user=Depends(get_current_user)):
    return user
