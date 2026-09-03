from constants import IngestType
from models import IngestHttp, Ingest
from models.ingest_http import (
    IngestHttpCreate,
    IngestHttpUpdate,
    IngestHttpRead,
)
from sqlmodel import Session, func

from sqlalchemy.orm import joinedload
from sqlalchemy import select
from fastapi import HTTPException
from typing import Optional

from models.filters import IngestFilter

from sorting import apply_sort_list
from fastapi_filters.ext.sqlalchemy import apply_filters

from validation import RepositoryValidator


class IngestHttpRepository:
    def __init__(self, session: Session):
        self.model = IngestHttp
        self.session = session

    def find_one(
        self, id: int, permission_group_ids_of_user: list[int]
    ) -> IngestHttp:
        statement = (
            select(self.model)
            .join(self.model.ingest)
            .where(self.model.ingest_id == id)
            .where(Ingest.permission_group_id.in_(permission_group_ids_of_user))
            .options(joinedload(self.model.ingest).joinedload(Ingest.permission_group))
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
            .join(self.model.ingest)
            .where(Ingest.permission_group_id.in_(permission_group_ids_of_user))
            .options(joinedload(self.model.ingest).joinedload(Ingest.permission_group))
        )

        if filters:
            statement = apply_filters(statement, filters)

        results = self.session.exec(statement).unique().scalars().all()
        flatt_list = [self.to_flat(item) for item in results]
        return apply_sort_list(flatt_list, sort_by) if sort_by else flatt_list

    def create(
        self,
        payload: IngestHttpCreate,
        extra_data,
        permission_group_ids_of_user: list[int],
    ) -> IngestHttp:

        RepositoryValidator.check_payload_permission_group(
            payload.permission_group_id, permission_group_ids_of_user
        )

        self.check_for_existing_name_create(payload.name, payload.permission_group_id)

        try:
            extra_data["ingest_type"] = IngestType.HTTP

            ingest = Ingest.model_validate(payload, update=extra_data)

            self.session.add(ingest)
            self.session.flush()

            extra_data["ingest_id"] = ingest.id

            ingest_http = IngestHttp.model_validate(
                payload, update=extra_data
            )

            self.session.add(ingest_http)

            self.session.commit()

            return ingest_http

        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to create.")

    def update(
        self,
        ingest_id: int,
        payload: IngestHttpUpdate,
        permission_group_ids_of_user: list[int],
    ) -> IngestHttp:

        if payload.permission_group_id is not None:
            RepositoryValidator.check_payload_permission_group(
                payload.permission_group_id, permission_group_ids_of_user
            )

        entity = self.find_one(ingest_id, permission_group_ids_of_user)

        ingest = entity.ingest

        self.check_for_existing_name_update(
            payload.name, ingest.permission_group_id, ingest.id
        )

        try:

            data = payload.model_dump(exclude_unset=True)

            # Update each entity with only its relevant fields
            ingest.sqlmodel_update(
                {
                    k: v
                    for k, v in data.items()
                    if k in {"name", "description", "permission_group_id", "parser_id"}
                }
            )

            entity.sqlmodel_update(
                {
                    k: v
                    for k, v in data.items()
                    if k
                    not in {"name", "description", "permission_group_id", "parser_id"}
                }
            )

            self.session.add(ingest)
            self.session.commit()
            self.session.refresh(ingest)
            self.session.refresh(entity)

            return entity

        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")

    def delete(self, ingest_id: int, permission_group_ids_of_user: list[int]):
        entity = self.find_one(ingest_id, permission_group_ids_of_user)

        # workaround as cascade delete doesn't seem to work currently
        ing = entity.ingest
        try:
            self.session.delete(entity)
            self.session.delete(ing)
            self.session.commit()
            return {"ok": True}
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to delete.")

    def check_for_existing_name_create(self, name_to_check, permission_group_id):

        statement = (
            select(self.model)
            .join(self.model.ingest)
            .where(
                Ingest.permission_group_id == permission_group_id,
                func.lower(Ingest.name) == func.lower(str(name_to_check)),
            )
            .options(joinedload(self.model.ingest).joinedload(Ingest.permission_group))
        )

        existing = self.session.exec(statement).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="This name already exists.")

    def check_for_existing_name_update(
        self, name_to_check, permission_group_id, entity_id
    ):

        statement = (
            select(self.model)
            .join(self.model.ingest)
            .where(
                Ingest.permission_group_id == permission_group_id,
                func.lower(Ingest.name) == func.lower(str(name_to_check)),
                Ingest.id != entity_id,
            )
            .options(joinedload(self.model.ingest).joinedload(Ingest.permission_group))
        )

        existing = self.session.exec(statement).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="This name already exists.")

    def to_flat(self, entity: IngestHttp) -> IngestHttpRead:
        ing = entity.ingest
        permission_group = ing.permission_group

        parser = ing.parser

        return IngestHttpRead(
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
            # http
            path_for_posts=entity.path_for_posts,
            file_type=entity.file_type,
            api_key=entity.api_key,
            enabled=entity.enabled,
            # Permission Group
            permission_group={
                "id": permission_group.id,
                "uuid": permission_group.uuid,
                "name": permission_group.name,
            },
            # Parser
            parser={**parser.parser_info},
        )
