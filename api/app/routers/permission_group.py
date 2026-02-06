from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..dependencies import get_session
from ..models.permission_group import PermissionGroup

router = APIRouter(
    prefix="/permission-group",
    tags= ["permission-groups"],
    responses={404: {"description": "Not found"}},
)

entity_name = "permission group"

@router.get("/", response_model=list[PermissionGroup], summary=f"Get a list of {entity_name}")
def read_list(
        *,
        session: Session = Depends(get_session)
):
    entities = session.exec(select(PermissionGroup)).all()
    return entities

@router.get("/{id}", response_model=PermissionGroup, summary=f"Get one {entity_name}")
def read_one(*, session: Session = Depends(get_session), id: int):
    entity = session.get(PermissionGroup, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity