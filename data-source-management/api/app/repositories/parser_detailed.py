from sqlmodel import Session
from models import ParserDetailed, Parser, User
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
from typing import Optional
from fastapi_filters.ext.sqlalchemy import apply_filters
from models.filters import ParserDetailedFilter
from models.parser_detailed import ParserDetailedRead
from fastapi_filters import FilterOperator
from sqlalchemy import cast, String
from sorting import apply_sort_list
from access_scope import AccessScope


class ParserDetailedRepository:
    def __init__(self, session: Session):
        self.model = ParserDetailed
        self.session = session

    def find_one(
        self,
        id: int,
        access_scope: AccessScope,
    ) -> ParserDetailed:
        statement = (
            select(self.model)
            .where(self.model.parser_id == id)
            .options(joinedload(self.model.parser).joinedload(Parser.ingest))
        )

        if not access_scope.is_superuser:
            statement = statement.where(
                self.model.permission_group_id.in_(access_scope.permission_group_ids)
            )
        entity = self.session.exec(statement).unique().scalar_one_or_none()
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        return entity

    def find_all(
        self,
        access_scope: AccessScope,
        sort_by: Optional[str] = None,
        filters: Optional[ParserDetailedFilter] = None,
    ):
        statement = (
            select(self.model)
            .options(joinedload(self.model.user))
            .options(joinedload(self.model.parser).joinedload(Parser.ingest))
        )

        if not access_scope.is_superuser:
            statement = statement.where(
                self.model.permission_group_id.in_(access_scope.permission_group_ids)
            )
        if filters:

            if filters.uuid and FilterOperator.ilike in filters.uuid:
                uuid_value = filters.uuid[FilterOperator.ilike]
                statement = statement.where(cast(Parser.uuid, String).ilike(uuid_value))
                filters.uuid = {}

            if filters.parser_type and FilterOperator.eq in filters.parser_type:
                statement = statement.where(
                    self.model.parser.has(
                        Parser.parser_type == filters.parser_type[FilterOperator.eq]
                    )
                )
                filters.parser_type = {}

            statement = apply_filters(statement, filters)

        results = self.session.exec(statement).unique().scalars().all()

        flatt_list = [self.to_flat(item) for item in results]
        return apply_sort_list(flatt_list, sort_by) if sort_by else flatt_list

    def delete(self, ingest_id: int, access_scope: AccessScope):
        entity = self.find_one(ingest_id, access_scope=access_scope)

        parser = entity.parser

        # don't delete parser that are connected to any ingest
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

    @staticmethod
    def to_flat(entity: ParserDetailed) -> ParserDetailedRead:

        parser = entity.parser

        user = entity.user

        permission_group = entity.permission_group

        return ParserDetailedRead(
            id=parser.id,
            parser_type=parser.parser_type,
            uuid=parser.uuid,
            created_at=entity.created_at,
            created_by=entity.created_by_id,
            name=entity.name,
            permission_group_id=entity.permission_group_id,
            description=entity.description,
            created_by_id=entity.created_by_id,
            permission_group={
                "id": permission_group.id,
                "uuid": permission_group.uuid,
                "name": permission_group.name,
            },
            created_by_username=user.username if user else None,
        )
        pass
