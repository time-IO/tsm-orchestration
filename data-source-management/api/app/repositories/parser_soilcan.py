from constants import ParserType
from models import ParserSoilcan, ParserDetailed, Parser
from models.parser_soilcan import (
    ParserSoilcanCreate,
    ParserSoilcanRead,
    ParserSoilcanUpdate,
)
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


class ParserSoilcanRepository:
    def __init__(self, session: Session):
        self.model = ParserSoilcan
        self.session = session

    def find_one(
        self,
        id: int,
        access_scope: AccessScope,
    ) -> ParserSoilcan:
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
        payload: ParserSoilcanCreate,
        extra_data: dict,
        access_scope: AccessScope,
    ):
        RepositoryValidator.check_payload_access_scope(
            payload.permission_group_id, access_scope
        )

        self.check_for_existing_name_create(payload.name, payload.permission_group_id)

        data = payload.model_dump(exclude={"timestamp_keys"})

        try:
            extra_data["parser_type"] = ParserType.SOILCAN

            ## create parser
            parser = Parser.model_validate(data, update=extra_data)
            self.session.add(parser)
            self.session.flush()

            extra_data["parser_id"] = parser.id

            ## create parser detail
            parser_detailed = ParserDetailed.model_validate(data, update=extra_data)
            self.session.add(parser_detailed)
            self.session.flush()

            # create parser_soilcan
            parser_soilcan = ParserSoilcan.model_validate(data, update=extra_data)
            self.session.add(parser_soilcan)
            self.session.flush()

            self.session.commit()
            return parser_soilcan
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to create parser")

    def update(
        self,
        parser_id: int,
        payload: ParserSoilcanUpdate,
        access_scope: AccessScope,
    ) -> ParserSoilcan:

        data = payload.model_dump(exclude_unset=True)

        parser_soilcan = self.find_one(parser_id, access_scope=access_scope)
        parser_detailed = parser_soilcan.parser_detailed

        self.check_for_existing_name_update(
            data["name"], parser_detailed.permission_group_id, parser_soilcan.parser_id
        )

        try:
            parser_detailed.sqlmodel_update(
                {k: v for k, v in data.items() if k in {"name", "description"}}
            )
            parser_soilcan.sqlmodel_update(
                {k: v for k, v in data.items() if k not in {"name", "description"}}
            )
            self.session.add(parser_detailed)
            self.session.add(parser_soilcan)

            self.session.commit()
            self.session.refresh(parser_detailed)
            self.session.refresh(parser_soilcan)

            return parser_soilcan
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")

    def delete(self, parser_id: int, access_scope: AccessScope):
        parser_soilcan = self.find_one(parser_id, access_scope=access_scope)

        parser_detailed = parser_soilcan.parser_detailed
        parser = parser_detailed.parser

        if parser.ingest:
            raise Exception(
                status_code=400,
                detail="Cannot delete parser that ist connected to an ingest",
            )

        try:
            self.session.delete(parser_soilcan)
            self.session.delete(parser_detailed)
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
    def to_flat(entity: ParserSoilcan) -> ParserSoilcanRead:
        parser_detailed = entity.parser_detailed
        parser = parser_detailed.parser
        permission_group = parser_detailed.permission_group

        return ParserSoilcanRead(
            id=parser.id,
            parser_type=parser.parser_type,
            uuid=parser_detailed.parser.uuid,
            created_at=parser_detailed.created_at,
            name=parser_detailed.name,
            permission_group_id=parser_detailed.permission_group_id,
            description=parser_detailed.description,
            created_by_id=parser_detailed.created_by_id,
            header=entity.header,
            type=entity.type,
            permission_group={
                "id": permission_group.id,
                "uuid": permission_group.uuid,
                "name": permission_group.name,
            },
        )
