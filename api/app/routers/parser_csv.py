from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from dependencies import (
    get_session,
    get_current_user,
    get_repo_ingest_csv_parser,
    get_repo_ingest_csv_parser_timestamp_column,
)
from models.parser_csv import (
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


@router.get("/{id}", response_model=CsvParserPublic, summary=f"Get one {entity_name}")
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
    except Exception as e:
        print(str(e))
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create {entity_name}")


@router.patch(
    "/{id}", summary=f"Update one {entity_name}", response_model=CsvParserPublic
)
def update(
    *,
    id: int,
    payload: CsvParserUpdate,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_csv_parser),
    session=Depends(get_session),
):

    # If timestamp_columns are provided, process them
    if payload.timestamp_columns is not None:
        # Validate that at least one timestamp column exists if provided
        if len(payload.timestamp_columns) == 0:
            raise HTTPException(
                status_code=400, detail="At least one timestamp column must be set"
            )
        try:
            # Delete all existing timestamp columns
            statement = select(CsvParserTimestampColumn).where(
                CsvParserTimestampColumn.csv_parser_id == id
            )
            existing_timestamp_columns = session.exec(statement).all()

            for tc in existing_timestamp_columns:
                session.delete(tc)

            # Create new timestamp columns
            parser_id_data = {"csv_parser_id": id}
            for timestamp in payload.timestamp_columns:
                db_timestamp = CsvParserTimestampColumn.model_validate(
                    timestamp, update=parser_id_data
                )
                session.add(db_timestamp)
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to update timestamp columns: {str(e)}"
            )

    # Remove timestamp_columns from payload before calling repo.update_allowed
    update_payload = payload.model_dump(
        exclude_unset=True, exclude={"timestamp_columns"}
    )

    # Call the repository update method
    return repo.update_parser(id, update_payload, current_user.permission_group_ids)


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_ingest_csv_parser),
):
    # todo: it should not be possible toi delete a parser that is connected to a s3store
    return repo.delete_allowed(id, current_user.permission_group_ids)
