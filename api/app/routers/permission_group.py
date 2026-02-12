from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..dependencies import get_session, get_current_user
from ..models.permission_group import PermissionGroup

router = APIRouter(
    prefix="/permission-group",
    tags=["permission-groups"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "permission group"


@router.get(
    "/", response_model=list[PermissionGroup], summary=f"Get a list of {entity_name}"
)
def read_list(
    *, session: Session = Depends(get_session), current_user=Depends(get_current_user)
):
    # A user should only see those permission groups he belongs to.
    # Use a WHERE IN statement via join to filter permission groups by current user's groups.
    statement = select(PermissionGroup).where(
        PermissionGroup.id.in_(current_user.permission_group_ids)
    )
    entities = session.exec(statement).all()
    return entities


@router.get("/{id}", response_model=PermissionGroup, summary=f"Get one {entity_name}")
def read_one(
    *,
    session: Session = Depends(get_session),
    id: int,
    current_user=Depends(get_current_user),
):
    # Only allow fetching permission groups the current user belongs to.
    statement = select(PermissionGroup).where(
        PermissionGroup.id == id,
        PermissionGroup.id.in_(current_user.permission_group_ids),
    )
    entity = session.exec(statement).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity
