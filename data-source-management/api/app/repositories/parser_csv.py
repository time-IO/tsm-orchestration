from constants import ParserType
from models import ParserCsv, ParserDetailed, Parser, ParserCsvTimestampColumn
from models.parser_csv import ParserCsvCreate, ParserCsvRead, ParserCsvUpdate
from sqlmodel import Session, func
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from fastapi import HTTPException
from typing import Optional
from access_scope import AccessScope

from models.filters import BaseFilter
from fastapi_filters.ext.sqlalchemy import apply_filters

from sorting import apply_sort_list
from validation import RepositoryValidator


class ParserCsvRepository:
    def __init__(self, session: Session):
        self.model = ParserCsv
        self.session = session

    def find_one(
        self,
        id: int,
        access_scope: AccessScope,
    ) -> ParserCsv:
        statement = (
            select(self.model)
            .join(self.model.parser_detailed)
            .where(self.model.parser_id == id)
            .options(
                joinedload(self.model.parser_detailed).joinedload(ParserDetailed.parser)
            )
        )

        if not access_scope.is_superuser:
            statement = statement.where(
                ParserDetailed.permission_group_id.in_(
                    access_scope.permission_group_ids
                )
            )

        entity = self.session.exec(statement).unique().scalar_one_or_none()
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        return entity

    def find_all(
        self,
        access_scope: AccessScope,
        sort_by: Optional[str] = None,
        filters: Optional[BaseFilter] = None,
    ):
        statement = (
            select(self.model)
            .join(self.model.parser_detailed)
            .join(ParserDetailed.parser)
            .options(
                joinedload(self.model.parser_detailed).joinedload(ParserDetailed.parser)
            )
        )

        if not access_scope.is_superuser:
            statement = statement.where(
                ParserDetailed.permission_group_id.in_(
                    access_scope.permission_group_ids
                )
            )

        if filters:
            statement = apply_filters(statement, filters)

        results = self.session.exec(statement).unique().scalars().all()
        flatt_list = [self.to_flat(item) for item in results]
        return apply_sort_list(flatt_list, sort_by) if sort_by else flatt_list

    def create(
        self,
        payload: ParserCsvCreate,
        extra_data,
        access_scope: AccessScope,
    ):

        RepositoryValidator.check_payload_access_scope(
            payload.permission_group_id, access_scope
        )

        self.check_for_existing_name_create(payload.name, payload.permission_group_id)

        if not payload.timestamp_columns:
            raise HTTPException(
                status_code=400, detail="At least one timestamp column must be set"
            )

        data = payload.model_dump(exclude={"timestamp_columns"})

        try:

            extra_data["parser_type"] = ParserType.CSV

            ## create parser
            parser = Parser.model_validate(data, update=extra_data)
            self.session.add(parser)
            self.session.flush()

            extra_data["parser_id"] = parser.id

            ## create parser detail
            parser_detailed = ParserDetailed.model_validate(data, update=extra_data)
            self.session.add(parser_detailed)
            self.session.flush()

            ## create parser csv
            parser_csv = ParserCsv.model_validate(data, update=extra_data)
            self.session.add(parser_csv)
            self.session.flush()

            ## create parser csv timestamp columns
            data_timestamp_column_extra = {"parser_csv_id": parser.id}

            for timestamp in payload.timestamp_columns:
                db_timestamp = ParserCsvTimestampColumn.model_validate(
                    timestamp, update=data_timestamp_column_extra
                )
                self.session.add(db_timestamp)

            self.session.commit()
            return parser_csv
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to create.")

    def update(
        self,
        parser_id: int,
        payload: ParserCsvUpdate,
        access_scope: AccessScope,
    ) -> ParserCsv:

        parser_csv = self.find_one(parser_id, access_scope=access_scope)

        self.update_timestamp_columns(payload, parser_id)

        data = payload.model_dump(exclude={"timestamp_columns"}, exclude_unset=True)

        parser_detailed = parser_csv.parser_detailed
        if "name" in payload:
            self.check_for_existing_name_update(
                data["name"], parser_detailed.permission_group_id, parser_csv.parser_id
            )

        try:
            parser_detailed.sqlmodel_update(
                {k: v for k, v in data.items() if k in {"name", "description"}}
            )

            parser_csv.sqlmodel_update(
                {k: v for k, v in data.items() if k not in {"name", "description"}}
            )
            self.session.add(parser_detailed)
            self.session.add(parser_csv)

            self.session.commit()

            self.session.refresh(parser_detailed)
            self.session.refresh(parser_csv)

            return parser_csv
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")

    def update_timestamp_columns(self, payload: ParserCsvUpdate, parser_id: int):

        if payload.timestamp_columns is not None:
            # Validate that at least one timestamp column exists if provided
            if len(payload.timestamp_columns) == 0:
                raise HTTPException(
                    status_code=400, detail="At least one timestamp column must be set"
                )
            try:
                # Delete all existing timestamp columns
                statement = select(ParserCsvTimestampColumn).where(
                    ParserCsvTimestampColumn.parser_csv_id == parser_id
                )
                existing_timestamp_columns = (
                    self.session.exec(statement).scalars().all()
                )

                for tc in existing_timestamp_columns:
                    self.session.delete(tc)

                # Create new timestamp columns
                parser_id_data = {"parser_csv_id": parser_id}
                for timestamp in payload.timestamp_columns:
                    db_timestamp = ParserCsvTimestampColumn.model_validate(
                        timestamp, update=parser_id_data
                    )
                    self.session.add(db_timestamp)
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update timestamp columns: {str(e)}",
                )

    def delete(self, parser_id: int, access_scope: AccessScope):
        parser_csv = self.find_one(parser_id, access_scope=access_scope)

        # workaround as cascade delete doesn't seem to work currently
        parser_detailed = parser_csv.parser_detailed
        parser = parser_detailed.parser

        if parser.ingest:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete parser that is connected to an ingest",
            )

        try:
            self.session.delete(parser)
            self.session.commit()
            return {"ok": True}
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to delete.")

    def check_for_existing_name_create(self, name_to_check, permission_group_id):

        clean_name = str(name_to_check).strip()

        statement = select(ParserDetailed).where(
            ParserDetailed.permission_group_id == permission_group_id,
            func.lower(ParserDetailed.name) == func.lower(clean_name),
        )

        existing = self.session.exec(statement).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="This name already exists.")

    def check_for_existing_name_update(
        self, name_to_check: str, permission_group_id: int, parser_id: int
    ):

        clean_name = str(name_to_check).strip()

        statement = select(ParserDetailed).where(
            ParserDetailed.permission_group_id == permission_group_id,
            func.lower(ParserDetailed.name) == func.lower(clean_name),
            ParserDetailed.parser_id != parser_id,
        )

        existing = self.session.exec(statement).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="This name already exists.")

    @staticmethod
    def to_flat(entity: ParserCsv) -> ParserCsvRead:
        parser_detailed = entity.parser_detailed
        parser = parser_detailed.parser
        permission_group = parser_detailed.permission_group

        return ParserCsvRead(
            id=parser.id,
            parser_type=parser.parser_type,
            uuid=parser.uuid,
            created_at=parser_detailed.created_at,
            name=parser_detailed.name,
            permission_group_id=parser_detailed.permission_group_id,
            description=parser_detailed.description,
            created_by_id=parser_detailed.created_by_id,
            timestamp_columns=entity.timestamp_columns,
            delimiter=entity.delimiter,
            timezone=entity.timezone,
            encoding=entity.encoding,
            headlines_to_exclude=entity.headlines_to_exclude,
            footlines_to_exclude=entity.footlines_to_exclude,
            pandas_read_csv=entity.pandas_read_csv,
            comment=entity.comment,
            header=entity.header,
            # Permission Group
            permission_group={
                "id": permission_group.id,
                "uuid": permission_group.uuid,
                "name": permission_group.name,
            },
        )
