from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..dependencies import get_session, get_current_user
from ..models.csv_parser import CsvParserCreate, CsvParser, CsvParserPublic, CsvParserTimestampColumn, CsvParserUpdate, \
    CsvParserTimestampColumnUpdate, CsvParserTimestampColumnPublic

router = APIRouter(
    prefix="/parser/csv",
    tags=["parser/csv"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)]
)

entity_name = "csv parser"


@router.get("/", response_model=list[CsvParserPublic], summary=f"Get a list of {entity_name}")
def read_list(
        *,
        session: Session = Depends(get_session)
):
    entities = session.exec(select(CsvParser)).all()
    return entities


@router.get("/{csvparser_id}", response_model=CsvParserPublic, summary=f"Get one {entity_name}")
def read_one(*, session: Session = Depends(get_session), csvparser_id: int):
    entity = session.get(CsvParser, csvparser_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity


@router.post("/", response_model=CsvParserPublic, summary=f"Create one {entity_name}")
def create(*, session: Session = Depends(get_session), payload: CsvParserCreate, user=Depends(get_current_user)):

    extra_data = {"created_by_id": user.id}

    # Validate manually before saving
    if not payload.timestamp_columns:
        raise HTTPException(
            status_code=400,
            detail="At least one timestamp column must be set"
        )

    data = payload.model_dump(exclude={"timestamp_columns"})

    entity = CsvParser.model_validate(data, update=extra_data)
    session.add(entity)
    session.flush()

    parser_id_data = {"csv_parser_id": entity.id}

    for timestamp in payload.timestamp_columns:
        db_timestamp = CsvParserTimestampColumn.model_validate(timestamp, update=parser_id_data)
        session.add(db_timestamp)

    session.commit()
    return entity


@router.patch("/{id}", summary=f"Update one {entity_name}")
def update(
        *, session: Session = Depends(get_session), id: int, payload: CsvParserUpdate
):
    entity = session.get(CsvParser, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    csvparser_data = payload.model_dump(exclude_unset=True)
    entity.sqlmodel_update(csvparser_data)
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(*, session: Session = Depends(get_session), id: int):
    entity = session.get(CsvParser, id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    session.delete(entity)
    session.commit()
    return {"ok": True}


@router.patch("/timestampcolumn/{timestampcolumn_id}", response_model=CsvParserTimestampColumnPublic,
              summary="Update one timestamp column of a csv parser")
def update_timestampcolumn(
        *, session: Session = Depends(get_session), timestampcolumn_id: int,
        payload: CsvParserTimestampColumnUpdate
):
    entity = session.get(CsvParserTimestampColumn, timestampcolumn_id)
    if not entity:
        raise HTTPException(status_code=404, detail="timestamp column not found")
    csvparsertimestamp_data = payload.model_dump(exclude_unset=True)
    entity.sqlmodel_update(csvparsertimestamp_data)
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


@router.delete("/timestampcolumn/{timestampcolumn_id}", summary="Delete one timestamp column of a csv parser")
def delete_timestampcolumn(*, session: Session = Depends(get_session), timestampcolumn_id: int):
    # Check if the timestamp column exists
    entity = session.get(CsvParserTimestampColumn, timestampcolumn_id)
    if not entity:
        raise HTTPException(status_code=404, detail="timestamp column not found")

    # Get the associated csv parser id
    csv_parser_id = entity.csv_parser_id

    # Check if there is more than one timestamp column for this parser
    remaining_timestamps = session.exec(
        select(CsvParserTimestampColumn)
        .where(CsvParserTimestampColumn.csv_parser_id == csv_parser_id)
        .where(CsvParserTimestampColumn.id != timestampcolumn_id)
    ).all()

    # If no remaining timestamp columns are found, raise an error
    if not remaining_timestamps:
        raise HTTPException(status_code=400,
                            detail="Can't delete the last timestamp column for this csv parser. At least one timestamp column must be set")

    # Delete the timestamp column
    session.delete(entity)
    session.commit()
    return {"ok": True}
