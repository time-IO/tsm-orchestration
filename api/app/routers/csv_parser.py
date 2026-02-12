from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from dependencies import (
    get_session,
    get_current_user,
    get_repo_ingest_csv_parser,
    get_repo_ingest_csv_parser_timestamp_column,
)
from models.csv_parser import (
    CsvParserCreate,
    CsvParser,
    CsvParserPublic,
    CsvParserTimestampColumn,
    CsvParserUpdate,
    CsvParserTimestampColumnUpdate,
    CsvParserTimestampColumnPublic,
)

router = APIRouter(
    prefix="/parser/csv",
    tags=["parser/csv"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "csv parser"


@router.get(
    "/", response_model=list[CsvParserPublic], summary=f"Get a list of {entity_name}"
)
def read_list(
    *,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_csv_parser),
):
    return repo.find_allowed_all(current_user.permission_group_ids)


@router.get(
    "/{csvparser_id}", response_model=CsvParserPublic, summary=f"Get one {entity_name}"
)
def read_one(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_csv_parser),
):
    return repo.find_allowed_one(id, current_user.permission_group_ids)


@router.post("/", response_model=CsvParserPublic, summary=f"Create one {entity_name}")
def create(
    *,
    session: Session = Depends(get_session),
    payload: CsvParserCreate,
    user=Depends(get_current_user),
):
    try:
        extra_data = {"created_by_id": user.id}

        # Validate manually before saving
        if not payload.timestamp_columns:
            raise HTTPException(
                status_code=400, detail="At least one timestamp column must be set"
            )

        data = payload.model_dump(exclude={"timestamp_columns"})

        entity = CsvParser.model_validate(data, update=extra_data)
        session.add(entity)
        session.flush()

        parser_id_data = {"csv_parser_id": entity.id}

        for timestamp in payload.timestamp_columns:
            db_timestamp = CsvParserTimestampColumn.model_validate(
                timestamp, update=parser_id_data
            )
            session.add(db_timestamp)

        session.commit()
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


@router.patch("/{id}", summary=f"Update one {entity_name}")
def update(
    *,
    id: int,
    payload: CsvParserUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_csv_parser),
):
    return repo.update_allowed(id, payload, current_user.permission_group_ids)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_csv_parser),
):
    return repo.delete_allowed(id, current_user.permission_group_ids)


@router.patch(
    "/timestampcolumn/{timestampcolumn_id}",
    response_model=CsvParserTimestampColumnPublic,
    summary="Update one timestamp column of a csv parser",
)
def update_timestampcolumn(
    *,
    timestampcolumn_id: int,
    payload: CsvParserTimestampColumnUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_csv_parser_timestamp_column),
):
    return repo.update_allowed(
        timestampcolumn_id, payload, current_user.permission_group_ids
    )


@router.delete(
    "/timestampcolumn/{timestampcolumn_id}",
    summary="Delete one timestamp column of a csv parser",
)
def delete_timestampcolumn(
    *, session: Session = Depends(get_session), timestampcolumn_id: int
):
    # Check if the timestamp column exists
    entity = session.get(CsvParserTimestampColumn, timestampcolumn_id)

    # todo check, that the current_user belongs to the permission group of the associated csvparser

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
        raise HTTPException(
            status_code=400,
            detail="Can't delete the last timestamp column for this csv parser. At least one timestamp column must be set",
        )

    # Delete the timestamp column
    session.delete(entity)
    session.commit()
    return {"ok": True}
