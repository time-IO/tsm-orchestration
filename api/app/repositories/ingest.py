from sqlalchemy.orm import joinedload
from sqlmodel import Session
from typing import Optional
from models import Ingest
from models.filters import IngestFilter
from sqlalchemy import select
from fastapi_filters.ext.sqlalchemy import apply_filters
from fastapi import HTTPException
from sqlalchemy import cast, String
from fastapi_filters import FilterOperator

from models.ingest import IngestWithApiInfoRead
from sorting import apply_sort_list


class IngestRepository:
    def __init__(self, session: Session):
        self.model = Ingest
        self.session = session

    def find_one(self, id: int, permission_group_ids_of_user: list[int]) -> Ingest:
        statement = (
            select(self.model)
            .where(
                self.model.id == id,
                self.model.permission_group_id.in_(permission_group_ids_of_user),
            )
            .options(joinedload(self.model.permission_group))
        )

        entity = self.session.exec(statement).unique().scalar_one_or_none()
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        return entity

    def find_all(
        self,
        permission_group_ids_of_user: list[int],
        sort_by: Optional[str] = None,
        filters: Optional[IngestFilter] = None,
    ):
        statement = (
            select(self.model)
            .where(self.model.permission_group_id.in_(permission_group_ids_of_user))
            .options(joinedload(self.model.external_api_detail))
            .options(joinedload(self.model.permission_group))
        )

        if filters:
            if filters.uuid and FilterOperator.ilike in filters.uuid:
                uuid_value = filters.uuid[FilterOperator.ilike]
                statement = statement.where(
                    cast(self.model.uuid, String).ilike(uuid_value)
                )
                filters.uuid = {}

            statement = apply_filters(statement, filters)

        results = self.session.exec(statement).unique().scalars().all()
        flatt_list = [self.to_flat(item) for item in results]
        return apply_sort_list(flatt_list, sort_by) if sort_by else flatt_list

    def delete(self, ingest_id: int, permission_group_ids_of_user: list[int]):
        entity = self.find_one(ingest_id, permission_group_ids_of_user)

        try:
            self.session.delete(entity)
            self.session.commit()
            return {"ok": True}
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to delete.")

    @staticmethod
    def to_flat(entity: Ingest) -> IngestWithApiInfoRead:

        permission_group = entity.permission_group

        external_api = entity.external_api_detail

        external_api_type = external_api.api_type if external_api is not None else None

        return IngestWithApiInfoRead(
            id=entity.id,
            uuid=entity.uuid,
            created_at=entity.created_at,
            ingest_type=entity.ingest_type,
            name=entity.name,
            permission_group_id=entity.permission_group_id,
            description=entity.description,
            created_by_id=entity.created_by_id,
            parser_id=entity.parser_id,
            permission_group={
                "id": permission_group.id,
                "uuid": permission_group.uuid,
                "name": permission_group.name,
            },
            external_api_type=external_api_type,
        )
