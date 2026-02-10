from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
from ..models.user import UserPublic

router = APIRouter(
    prefix="/me",
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=UserPublic)
def read_user(user=Depends(get_current_user)):
    return user
