from fastapi import APIRouter, Depends
from access_scope import AccessScope
from dependencies import get_current_user, get_repo_permission_group
from models.filters import PermissionGroupFilter
from models.permission_group import PermissionGroup
from models import User
from fastapi_pagination import Page
from fastapi_pagination import paginate

router = APIRouter(
    prefix="/permission-group",
    tags=["permission-groups"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "permission group"


@router.get(
    "/", response_model=Page[PermissionGroup], summary=f"Get a list of {entity_name}"
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_repo_permission_group),
    filters: PermissionGroupFilter = Depends(),
    sort_by: str | None = None,
):
    return paginate(
        repo.find_allowed_all(
            sort_by=sort_by,
            filters=filters,
            access_scope=AccessScope.from_user(current_user),
        )
    )


@router.get("/{id}", response_model=PermissionGroup, summary=f"Get one {entity_name}")
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_repo_permission_group),
):
    return repo.find_allowed_one(id, access_scope=AccessScope.from_user(current_user))
