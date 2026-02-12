from fastapi import APIRouter
from models.health import Health

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=Health, summary="Check if api is up and running")
def health_check():
    return {"status": "ok"}
