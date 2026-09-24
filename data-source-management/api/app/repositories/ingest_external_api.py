from sqlalchemy.orm import joinedload
from sqlmodel import Session
from typing import Optional
from models import IngestExternalApi, Ingest
from models.filters import IngestExternalApiFilter
from sqlalchemy import select
from fastapi_filters.ext.sqlalchemy import apply_filters
from fastapi import HTTPException
from sqlalchemy import cast, String
from fastapi_filters import FilterOperator

from access_scope import AccessScope
from models.ingest_external_api import IngestExternalApiRead
from sorting import apply_sort_list


class IngestExternalApiRepository:
    def __init__(self, session: Session):
        self.model = IngestExternalApi
        self.session = session

    def find_one(self, id: int, access_scope: AccessScope) -> IngestExternalApi:
        statement = (
            select(self.model)
            .join(self.model.ingest)
            .where(self.model.ingest_id == id)
            .options(joinedload(self.model.ingest).joinedload(Ingest.permission_group))
        )

        if not access_scope.is_superuser:
            statement = statement.where(
                Ingest.permission_group_id.in_(access_scope.permission_group_ids)
            )

        entity = self.session.exec(statement).unique().scalar_one_or_none()
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        return entity

    def find_all(
        self,
        access_scope: AccessScope,
        sort_by: Optional[str] = None,
        filters: Optional[IngestExternalApiFilter] = None,
    ):
        statement = (
            select(self.model)
            .join(self.model.ingest)
            .options(joinedload(self.model.ingest).joinedload(Ingest.permission_group))
        )

        if not access_scope.is_superuser:
            statement = statement.where(
                Ingest.permission_group_id.in_(access_scope.permission_group_ids)
            )

        if filters:
            if filters.uuid and FilterOperator.ilike in filters.uuid:
                uuid_value = filters.uuid[FilterOperator.ilike]
                statement = statement.where(cast(Ingest.uuid, String).ilike(uuid_value))
                filters.uuid = {}
            statement = apply_filters(statement, filters)

        results = self.session.exec(statement).unique().scalars().all()
        flatt_list = [self.to_flat(item) for item in results]
        return apply_sort_list(flatt_list, sort_by) if sort_by else flatt_list

    def delete(self, ingest_id: int, access_scope: AccessScope):
        entity = self.find_one(ingest_id, access_scope=access_scope)

        try:
            self.session.delete(entity)
            self.session.commit()
            return {"ok": True}
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to delete.")

    @staticmethod
    def to_flat(entity: IngestExternalApi) -> IngestExternalApiRead:

        ing = entity.ingest

        permission_group = ing.permission_group

        return IngestExternalApiRead(
            # Ingest
            id=ing.id,
            uuid=ing.uuid,
            created_at=ing.created_at,
            ingest_type=ing.ingest_type,
            name=ing.name,
            permission_group_id=ing.permission_group_id,
            description=ing.description,
            created_by_id=ing.created_by_id,
            parser_id=ing.parser_id,
            # External API
            api_type=entity.api_type,
            sync_enabled=entity.sync_enabled,
            sync_interval_in_minutes=entity.sync_interval_in_minutes,
            permission_group={
                "id": permission_group.id,
                "uuid": permission_group.uuid,
                "name": permission_group.name,
            },
        )
