from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..dependencies import get_session, get_current_user
from ..models.ingest_s3store import (
    IngestS3Store,
    IngestS3StoreCreate,
    IngestS3StorePublic,
    IngestS3StoreUpdate,
)

router = APIRouter(
    prefix="/ingest/s3store",
    tags=["ingest/s3store"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest s3store"


@router.get(
    "/",
    response_model=list[IngestS3StorePublic],
    summary=f"Get a list of {entity_name}",
)
def read_list(*, session: Session = Depends(get_session)):
    entities = session.exec(select(IngestS3Store)).all()
    return entities


@router.get(
    "/{id}", response_model=IngestS3StorePublic, summary=f"Get one {entity_name}"
)
def read_one(*, session: Session = Depends(get_session), id: int):
    entity = session.get(IngestS3Store, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity


@router.post(
    "/", response_model=IngestS3StorePublic, summary=f"Create one {entity_name}"
)
def create(
    *,
    session: Session = Depends(get_session),
    payload: IngestS3StoreCreate,
    user=Depends(get_current_user),
):
    extra_data = {"created_by_id": user.id}

    # todo create username, password (+ encrypt), bucket_name

    entity = IngestS3Store.model_validate(payload, update=extra_data)
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


@router.patch(
    "/{id}", response_model=IngestS3StorePublic, summary=f"Update one {entity_name}"
)
def update_ingests3store(
    *, session: Session = Depends(get_session), id: int, payload: IngestS3StoreUpdate
):
    entity = session.get(IngestS3Store, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    ingests3store_data = payload.model_dump(exclude_unset=True)
    entity.sqlmodel_update(ingests3store_data)
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete_ingests3store(*, session: Session = Depends(get_session), id: int):
    entity = session.get(IngestS3Store, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    session.delete(entity)
    session.commit()
    return {"ok": True}
