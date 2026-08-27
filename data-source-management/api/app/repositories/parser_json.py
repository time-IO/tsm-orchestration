from constants import ParserType
from models import ParserJson, ParserDetailed, Parser, ParserJsonTimestampKey
from models.parser_json import ParserJsonCreate, ParserJsonRead, ParserJsonUpdate
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


class ParserJsonRepository:
    def __init__(self, session: Session):
        self.model = ParserJson
        self.session = session

    def find_one(
        self,
        id: int,
        access_scope: AccessScope,
    ) -> ParserJson:
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
        flat_list = [self.to_flat(item) for item in results]
        return apply_sort_list(flat_list, sort_by) if sort_by else flat_list

    def create(
        self,
        payload: ParserJsonCreate,
        extra_data: dict,
        access_scope: AccessScope,
    ):
        RepositoryValidator.check_payload_access_scope(
            payload.permission_group_id, access_scope
        )

        self.check_for_existing_name_create(payload.name, payload.permission_group_id)

        if not payload.timestamp_keys:
            raise HTTPException(
                status_code=400, detail="At least one timestamp key must be set"
            )

        data = payload.model_dump(exclude={"timestamp_keys"})

        try:
            extra_data["parser_type"] = ParserType.JSON

            ## create parser
            parser = Parser.model_validate(data, update=extra_data)
            self.session.add(parser)
            self.session.flush()

            extra_data["parser_id"] = parser.id

            ## create parser detail
            parser_detailed = ParserDetailed.model_validate(data, update=extra_data)
            self.session.add(parser_detailed)
            self.session.flush()

            # create parser_json
            parser_json = ParserJson.model_validate(data, update=extra_data)
            self.session.add(parser_json)
            self.session.flush()

            # create timestamp keys
            timestamp_key_extra = {"parser_json_id": parser.id}
            for ts_key in payload.timestamp_keys:
                db_ts_key = ParserJsonTimestampKey.model_validate(
                    ts_key, update=timestamp_key_extra
                )
                self.session.add(db_ts_key)
            self.session.commit()
            return parser_json
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to create parser")

    def update(
        self,
        parser_id: int,
        payload: ParserJsonUpdate,
        access_scope: AccessScope,
    ) -> ParserJson:

        parser_json = self.find_one(parser_id, access_scope=access_scope)

        self.update_timestamp_keys(payload, parser_id)

        data = payload.model_dump(exclude={"timestamp_keys"}, exclude_unset=True)

        parser_detailed = parser_json.parser_detailed

        if "name" in payload:
            self.check_for_existing_name_update(
                data["name"], parser_detailed.permission_group_id, parser_json.parser_id
            )

        try:
            parser_detailed.sqlmodel_update(
                {k: v for k, v in data.items() if k in {"name", "description"}}
            )
            parser_json.sqlmodel_update(
                {k: v for k, v in data.items() if k not in {"name", "description"}}
            )
            self.session.add(parser_detailed)
            self.session.add(parser_json)

            self.session.commit()
            self.session.refresh(parser_detailed)
            self.session.refresh(parser_json)

            return parser_json
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")

    def update_timestamp_keys(self, payload: ParserJsonUpdate, parser_id: int):
        if payload.timestamp_keys is not None:
            if len(payload.timestamp_keys) == 0:
                raise HTTPException(
                    status_code=400, detail="At least one timestamp key must be set."
                )
            try:
                # Delete all existing timestamp columns
                statement = select(ParserJsonTimestampKey).where(
                    ParserJsonTimestampKey.parser_json_id == parser_id
                )
                existing = self.session.exec(statement).scalars().all()

                for tk in existing:
                    self.session.delete(tk)

                # Create new timestamp columns
                ts_key_extra = {"parser_json_id": parser_id}
                for ts_key in payload.timestamp_keys:
                    db_ts_key = ParserJsonTimestampKey.model_validate(
                        ts_key, update=ts_key_extra
                    )
                    self.session.add(db_ts_key)

                self.session.commit()
            except Exception as e:
                self.session.rollback()
                raise HTTPException(
                    status_code=500, detail=f"Failed to update timestamp keys: {str(e)}"
                )

    def delete(self, parser_id: int, access_scope: AccessScope):
        parser_json = self.find_one(parser_id, access_scope=access_scope)

        parser_detailed = parser_json.parser_detailed
        parser = parser_detailed.parser

        if parser.ingest:
            raise Exception(
                status_code=400,
                detail="Cannot delete parser that ist connected to an ingest",
            )

        try:
            self.session.delete(parser)
            self.session.commit()
            return {"ok": True}
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to delete parser.")

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
    def to_flat(entity: ParserJson) -> ParserJsonRead:
        parser_detailed = entity.parser_detailed
        parser = parser_detailed.parser
        permission_group = parser_detailed.permission_group

        return ParserJsonRead(
            id=parser.id,
            parser_type=parser.parser_type,
            uuid=parser_detailed.parser.uuid,
            created_at=parser_detailed.created_at,
            name=parser_detailed.name,
            permission_group_id=parser_detailed.permission_group_id,
            description=parser_detailed.description,
            created_by_id=parser_detailed.created_by_id,
            comment=entity.comment,
            timestamp_keys=entity.timestamp_keys,
            timezone=entity.timezone,
            permission_group={
                "id": permission_group.id,
                "uuid": permission_group.uuid,
                "name": permission_group.name,
            },
        )
