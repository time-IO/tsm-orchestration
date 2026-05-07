from fastapi import APIRouter, Depends
from dependencies import get_current_user
from utils import encodings

router = APIRouter(
    prefix="/parser_encoding",
    tags=["parser_encoding"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/",
    summary=f"Get a list of file encoding suitable for parser",
)
def read_list():
    return encodings
