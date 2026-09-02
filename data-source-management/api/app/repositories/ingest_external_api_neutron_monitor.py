from constants import ApiType, IngestType
from models import IngestExternalApiNeutronMonitor, IngestExternalApi, Ingest
from models.ingest_external_api_neutron_monitor import (
    IngestExternalApiNeutronMonitorRead,
    IngestExternalApiNeutronMonitorUpdate,
)
from typing import Optional
from sqlmodel import Session, func
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from fastapi import HTTPException
from access_scope import AccessScope

from models.filters import IngestExternalApiFilter
from sorting import apply_sort_list
from fastapi_filters.ext.sqlalchemy import apply_filters

from validation import RepositoryValidator


class IngestExternalApiNeutronMonitorRepository:
    def __init__(self, session: Session):
        self.model = IngestExternalApiNeutronMonitor
        self.session = session

    def find_one(
        self,
        id: int,
        access_scope: AccessScope,
    ) -> IngestExternalApiNeutronMonitor:

        statement = (
            select(self.model)
            .join(self.model.external_api)
            .join(IngestExternalApi.ingest)
            .where(self.model.ingest_id == id)
            .options(
                joinedload(self.model.external_api)
                .joinedload(IngestExternalApi.ingest)
                .joinedload(Ingest.permission_group)
            )
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
            .join(self.model.external_api)
            .join(IngestExternalApi.ingest)
            .options(
                joinedload(self.model.external_api)
                .joinedload(IngestExternalApi.ingest)
                .joinedload(Ingest.permission_group)
            )
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
    ) -> IngestExternalApiNeutronMonitor:

        RepositoryValidator.check_payload_access_scope(
            payload.permission_group_id, access_scope
        )

        self.check_for_existing_name_create(payload.name, payload.permission_group_id)

        try:
            extra_data["ingest_type"] = IngestType.EXTERNAL_API

            ingest = Ingest.model_validate(payload, update=extra_data)

            self.session.add(ingest)
            self.session.flush()

            data_ingest_external_api = {
                "api_type": ApiType.NEUTRON_MONITOR,
                "ingest_id": ingest.id,
            }
            ingest_external_api = IngestExternalApi.model_validate(
                payload, update=data_ingest_external_api
            )

            self.session.add(ingest_external_api)
            self.session.flush()

            data_ingest_external_api_nm = {"ingest_id": ingest.id}
            ingest_external_api_nm = IngestExternalApiNeutronMonitor.model_validate(
                payload, update=data_ingest_external_api_nm
            )

            self.session.add(ingest_external_api_nm)

            self.session.commit()

            return ingest_external_api_nm

        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to create.")

    def update(
        self,
        ingest_id: int,
        payload: IngestExternalApiNeutronMonitorUpdate,
        access_scope: AccessScope,
    ) -> IngestExternalApiNeutronMonitor:

        if payload.permission_group_id is not None:
            RepositoryValidator.check_payload_access_scope(
                payload.permission_group_id, access_scope
            )

        entity = self.find_one(ingest_id, access_scope=access_scope)

        ingest = entity.external_api.ingest

        self.check_for_existing_name_update(
            payload.name, ingest.permission_group_id, ingest.id
        )

        try:

            ext_api = entity.external_api

            data = payload.model_dump(exclude_unset=True)

            # Update each entity with only its relevant fields
            ingest.sqlmodel_update(
                {
                    k: v
                    for k, v in data.items()
                    if k in {"name", "description", "permission_group_id", "parser_id"}
                }
            )

            ext_api.sqlmodel_update(
                {
                    k: v
                    for k, v in data.items()
                    if k in {"sync_enabled", "sync_interval_in_minutes"}
                }
            )

            entity.sqlmodel_update(
                {
                    k: v
                    for k, v in data.items()
                    if k
                    not in {
                        "name",
                        "description",
                        "permission_group_id",
                        "parser_id",
                        "sync_enabled",
                        "sync_interval_in_minutes",
                    }
                }
            )

            self.session.add(ingest)
            self.session.add(ext_api)
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(ingest)
            self.session.refresh(ext_api)
            self.session.refresh(entity)

            return entity

        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")

    def delete(self, ingest_id: int, access_scope: AccessScope):
        entity = self.find_one(ingest_id, access_scope=access_scope)

        # workaround as cascade delete doesn't seem to work currently
        ext = entity.external_api
        ing = ext.ingest

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

    @staticmethod
    def to_flat(
        nm: IngestExternalApiNeutronMonitor,
    ) -> IngestExternalApiNeutronMonitorRead:
        ext = nm.external_api
        ing = ext.ingest
        permission_group = ing.permission_group

        return IngestExternalApiNeutronMonitorRead(
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
            api_type=ext.api_type,
            sync_enabled=ext.sync_enabled,
            sync_interval_in_minutes=ext.sync_interval_in_minutes,
            # NeutronMonitor
            station_id=nm.station_id,
            time_resolution_in_minutes=nm.time_resolution_in_minutes,
            station={
                "id": nm.station.id,
                "station_id": nm.station.station_id,
                "description": nm.station.description,
            },
            # Permission Group
            permission_group={
                "id": permission_group.id,
                "uuid": permission_group.uuid,
                "name": permission_group.name,
            },
        )
