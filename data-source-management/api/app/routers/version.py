from config import settings
from fastapi import APIRouter
from models.version import Version

router = APIRouter(
    prefix="/version",
    tags=["version"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=Version, summary="Get the deployed API version")
def get_version():
    return {"version": settings.API_VERSION}
