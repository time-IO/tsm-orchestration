from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..dependencies import get_session
from ..models.project import Project

router = APIRouter(
    prefix="/projects",
    tags= ["projects"],
    responses={404: {"description": "Not found"}},
)

entity_name = "project"

@router.get("/", response_model=list[Project], summary=f"Get a list of {entity_name}")
def read_list(
        *,
        session: Session = Depends(get_session)
):
    entities = session.exec(select(Project)).all()
    return entities

@router.get("/{id}", response_model=Project, summary=f"Get one {entity_name}")
def read_one(*, session: Session = Depends(get_session), id: int):
    entity = session.get(Project, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity