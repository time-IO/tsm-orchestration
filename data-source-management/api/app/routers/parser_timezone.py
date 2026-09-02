import pytz
from fastapi import APIRouter, Depends
from dependencies import get_current_user

router = APIRouter(
    prefix="/parser_timezone",
    tags=["parser_timezone"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/",
    summary=f"Get a list of parser timezones",
)
def read_list():
    # Move "UTC" and "Europe/Berlin" to the beginning
    reordered = ["UTC", "Europe/Berlin"]
    reordered.extend(tz for tz in pytz.all_timezones if tz not in reordered)
    return reordered
