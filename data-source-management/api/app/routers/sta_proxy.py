from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from access_scope import AccessScope
from dependencies import bearer_scheme, get_current_user, get_repo_database
from models import User
from services import sta_proxy_service

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
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    # requests without a token are rejected already
    return await sta_proxy_service(
        permission_group_id=permission_group_id,
        query=q,
        access_scope=AccessScope.from_user(current_user),
        repo_database=repo,
        token=credentials.credentials,
    )
