from sqlmodel import Session, func

from constants import IngestType
from models import IngestMqtt, Ingest
from models.ingest import IngestUpdate
from models.ingest_mqtt import IngestMqttRead
from models.filters import IngestFilter
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from fastapi import HTTPException
from typing import Optional
from access_scope import AccessScope

from sorting import apply_sort_list
from fastapi_filters.ext.sqlalchemy import apply_filters

from validation import RepositoryValidator


class IngestMqttRepository:
    def __init__(self, session: Session):
        self.model = IngestMqtt
        self.session = session

    def find_one(
        self,
        id: int,
        access_scope: AccessScope,
    ) -> IngestMqtt:
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
        filters: Optional[IngestFilter] = None,
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
            statement = apply_filters(statement, filters)

        results = self.session.exec(statement).unique().scalars().all()
        flatt_list = [self.to_flat(item) for item in results]
        return apply_sort_list(flatt_list, sort_by) if sort_by else flatt_list

    def create(
        self,
        payload,
        extra_data,
        access_scope: AccessScope,
    ) -> IngestMqtt:

        RepositoryValidator.check_payload_access_scope(
            payload.permission_group_id, access_scope
        )

        self.check_for_existing_name_create(payload.name, payload.permission_group_id)
        self.check_for_existing_username_create(extra_data["username"])

        try:
            extra_data["ingest_type"] = IngestType.MQTT

            ingest = Ingest.model_validate(payload, update=extra_data)

            self.session.add(ingest)
            self.session.flush()

            extra_data["ingest_id"] = ingest.id

            ingest_mqtt = IngestMqtt.model_validate(payload, update=extra_data)

            self.session.add(ingest_mqtt)

            self.session.commit()

            return ingest_mqtt

        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to create.")

    def update(
        self,
        ingest_id: int,
        payload: IngestUpdate,
        access_scope: AccessScope,
    ) -> IngestMqtt:

        if payload.permission_group_id is not None:
            RepositoryValidator.check_payload_access_scope(
                payload.permission_group_id, access_scope
            )

        entity = self.find_one(ingest_id, access_scope=access_scope)

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

            self.session.add(ingest)
            self.session.commit()
            self.session.refresh(ingest)
            self.session.refresh(entity)

            return entity

        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")

    def delete(self, ingest_id: int, access_scope: AccessScope):
        entity = self.find_one(ingest_id, access_scope=access_scope)

        # workaround as cascade delete doesn't seem to work currently
        ing = entity.ingest

        try:
            self.session.delete(ing)
            self.session.commit()
            return {"ok": True}
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to delete.")

    def check_for_existing_name_create(self, name_to_check, permission_group_id):

        clean_name = str(name_to_check).strip()

        statement = (
            select(Ingest)
            .where(
                Ingest.permission_group_id == permission_group_id,
                func.lower(Ingest.name) == func.lower(clean_name),
            )
            .options(joinedload(Ingest.permission_group))
        )

        existing = self.session.exec(statement).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="This name already exists.")

    def check_for_existing_name_update(
        self, name_to_check, permission_group_id, entity_id
    ):

        clean_name = str(name_to_check).strip()

        statement = (
            select(Ingest)
            .where(
                Ingest.permission_group_id == permission_group_id,
                func.lower(Ingest.name) == func.lower(clean_name),
                Ingest.id != entity_id,
            )
            .options(joinedload(Ingest.permission_group))
        )

        existing = self.session.exec(statement).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="This name already exists.")

    def check_for_existing_username_create(self, username_to_check: str):

        clean_name = str(username_to_check).strip()

        statement = select(self.model).where(
            func.lower(self.model.username) == func.lower(clean_name)
        )

        existing = self.session.exec(statement).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="This username already exists.")

    @staticmethod
    def to_flat(entity: IngestMqtt) -> IngestMqttRead:
        ing = entity.ingest
        permission_group = ing.permission_group

        parser = ing.parser

        return IngestMqttRead(
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
            # Mqtt
            topic=entity.topic,
            uri=entity.uri,
            username=entity.username,
            password=entity.password,
            password_hashed=entity.password_hashed,
            # parser
            parser={**parser.parser_info},
            # Permission Group
            permission_group={
                "id": permission_group.id,
                "uuid": permission_group.uuid,
                "name": permission_group.name,
            },
        )
