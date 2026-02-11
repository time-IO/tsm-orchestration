from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from ..dependencies import get_session, get_current_user
from ..models.ingest_external_api_bosch import (
    IngestExternalApiBoschCreate,
    IngestExternalApiBosch,
    IngestExternalApiBoschUpdate,
    IngestExternalApiBoschPublic,
)

router = APIRouter(
    prefix="/ingest/external-api/bosch",
    tags=["ingest/external-api/bosch"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest external api bosch"


@router.get(
    "/",
    response_model=list[IngestExternalApiBoschPublic],
    summary=f"Get a list of {entity_name}",
)
def read_list(*, session: Session = Depends(get_session)):
    entities = session.exec(select(IngestExternalApiBosch)).all()
    return entities


@router.get(
    "/{id}",
    response_model=IngestExternalApiBoschPublic,
    summary=f"Get one {entity_name}",
)
def read_one(*, session: Session = Depends(get_session), id: int):
    entity = session.get(IngestExternalApiBosch, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity


@router.post(
    "/",
    response_model=IngestExternalApiBoschPublic,
    summary=f"Create one {entity_name}",
)
def create(
    *,
    session: Session = Depends(get_session),
    payload: IngestExternalApiBoschCreate,
    user=Depends(get_current_user),
):
    try:
        extra_data = {"created_by_id": user.id}
        entity = IngestExternalApiBosch.model_validate(payload, update=extra_data)
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"{entity_name} with the same name and permission group already exists.",
        )
    except:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create {entity_name}")


@router.patch(
    "/{id}",
    response_model=IngestExternalApiBoschPublic,
    summary=f"Update one {entity_name}",
)
def update(
    *,
    session: Session = Depends(get_session),
    id: int,
    payload: IngestExternalApiBoschUpdate,
):
    try:
        entity = session.get(IngestExternalApiBosch, id)
        if not entity:
            raise HTTPException(status_code=404, detail=f"{entity_name} not found")
        data = payload.model_dump(exclude_unset=True)
        entity.sqlmodel_update(data)
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"{entity_name} with the same name and permission group already exists.",
        )
    except:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update {entity_name}")


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(*, session: Session = Depends(get_session), id: int):
    entity = session.get(IngestExternalApiBosch, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    session.delete(entity)
    session.commit()
    return {"ok": True}
