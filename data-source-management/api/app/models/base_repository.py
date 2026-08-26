from typing import Type, TypeVar, Generic, List, Optional
from fastapi_filters import FilterSet
from fastapi_filters.ext.sqlalchemy import apply_filters
from sqlmodel import Session, select, SQLModel, func
from fastapi import HTTPException

from .quality_control_setting import (
    QualityControlSetting,
    QualityControlFunction,
    QualityControlFunctionArgument,
)
from .permission_group import PermissionGroup
from .database import Database
from utils import create_db_username, generate_password
from sorting import apply_sort_list
from config import settings
from mqtt import publish_frontend_thing_update
from sqlalchemy.orm import joinedload

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def find_one(self, id: int):
        entity = self.session.get(self.model, id)
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        return entity

    def find_all(self, filters: FilterSet | None = None):
        statement = select(self.model)

        if filters:
            statement = apply_filters(statement, filters)

        return self.session.exec(statement).all()

    def find_allowed_one(self, id: int, permission_group_ids: list[int]) -> T:
        statement = select(self.model).where(
            self.model.id == id,
            self.model.permission_group_id.in_(permission_group_ids),
        )
        entity = self.session.exec(statement).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        return entity

    def find_allowed_all(
        self,
        permission_group_ids: list[int],
        sort_by: Optional[str] = None,
        filters: FilterSet | None = None,
    ) -> List[T]:
        statement = select(self.model).where(
            self.model.permission_group_id.in_(permission_group_ids)
        )
        if filters:
            statement = apply_filters(statement, filters)
        items = self.session.exec(statement).all()
        return apply_sort_list(items, sort_by) if sort_by else items

    def check_for_existing_name(self, name_to_check, permission_group_id):
        existing_statement = select(self.model).where(
            func.lower(self.model.name) == func.lower(str(name_to_check)),
            self.model.permission_group_id == permission_group_id,
        )
        existing = self.session.exec(existing_statement).first()
        if existing:
            raise HTTPException(status_code=400, detail="This name already exists.")

    def check_for_existing_name_update(
        self, name_to_check, permission_group_id, entity_id
    ):
        existing_statement = select(self.model).where(
            func.lower(self.model.name) == func.lower(str(name_to_check)),
            self.model.permission_group_id == permission_group_id,
            self.model.id != entity_id,
        )
        existing = self.session.exec(existing_statement).first()
        if existing:
            raise HTTPException(status_code=400, detail="This name already exists.")

    def create_allowed(
        self, payload, extra_data, permission_group_ids, ingest_type_info=None
    ):
        self.check_payload_permission_group(
            payload.permission_group_id, permission_group_ids
        )

        self.check_for_existing_name(payload.name, payload.permission_group_id)

        try:
            entity = self.model.model_validate(payload, update=extra_data)
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            if ingest_type_info:
                publish_frontend_thing_update(entity, ingest_type_info)
            return entity
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to create.")

    def update_allowed(
        self, id: int, payload, permission_group_ids, ingest_type_info=None
    ):
        self.check_payload_permission_group(
            payload.permission_group_id, permission_group_ids
        )
        try:
            entity = self.find_allowed_one(id, permission_group_ids)

            if not entity:
                raise HTTPException(status_code=404, detail="Not found")

            self.check_for_existing_name_update(
                payload.name, entity.permission_group_id, entity.id
            )

            data = payload.model_dump(exclude_unset=True)
            entity.sqlmodel_update(data)
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            if ingest_type_info:
                publish_frontend_thing_update(entity, ingest_type_info)
            return entity
        except HTTPException as exception:
            raise exception
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")

    def update_parser(self, id: int, data, permission_group_ids):

        try:
            entity = self.find_allowed_one(id, permission_group_ids)

            if not entity:
                raise HTTPException(status_code=404, detail="Not found")

            self.check_for_existing_name_update(
                data["name"], entity.permission_group_id, entity.id
            )

            entity.sqlmodel_update(data)
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except HTTPException as exception:
            raise exception
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")

    def delete_allowed(self, id: int, permission_group_ids):
        entity = self.find_allowed_one(id, permission_group_ids)
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        self.session.delete(entity)
        self.session.commit()
        return {"ok": True}

    @staticmethod
    def check_payload_permission_group(
        permission_group_id_to_check: int, permission_group_ids: list[int]
    ):
        if permission_group_id_to_check not in permission_group_ids:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: user does not belong to that permission group.",
            )


class PermissionGroupRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(model=PermissionGroup, session=session)

    def find_allowed_one(self, id: int, permission_group_ids: list[int]) -> T:
        statement = select(self.model).where(
            self.model.id == id,
            self.model.id.in_(permission_group_ids),
        )
        entity = self.session.exec(statement).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        return entity

    def find_allowed_all(
        self,
        permission_group_ids: list[int],
        sort_by: Optional[str] = None,
        filters: FilterSet | None = None,
    ) -> List[T]:
        statement = select(self.model).where(self.model.id.in_(permission_group_ids))

        if filters:
            statement = apply_filters(statement, filters)

        items = self.session.exec(statement).all()
        return apply_sort_list(items, sort_by) if sort_by else items


class DatabaseRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(model=Database, session=session)

    def find_one_permission_group_id(self, permission_group_id: int):
        statement = select(self.model).where(
            self.model.permission_group_id == permission_group_id
        )
        return self.session.exec(statement).first()

    def create(
        self, permission_group: PermissionGroup, permission_group_ids: list[int]
    ):

        self.check_payload_permission_group(permission_group.id, permission_group_ids)

        try:
            database = Database()
            database.permission_group_id = permission_group.id
            database.name = settings.POSTGRES_DB
            database.username = create_db_username(permission_group.name, False)
            database.url = f"postgresql://{database.username}@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"
            database.read_only_username = create_db_username(
                permission_group.name, True
            )
            database.read_only_url = f"postgresql://{database.read_only_username}@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"
            database.password = generate_password(24)
            database.read_only_password = generate_password(24)

            self.session.add(database)
            self.session.commit()
            print(
                f"Successfully created new database entity for permission_group_id:{permission_group.id}"
            )
        except Exception as e:
            print("Failed to create database entity")
            print(str(e))
            self.session.rollback()


class QualityControlSettingRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(model=QualityControlSetting, session=session)

    def find_allowed_all(
        self,
        permission_group_ids: list[int],
        sort_by: Optional[str] = None,
        filters: FilterSet | None = None,
    ) -> List[T]:
        statement = (
            select(self.model)
            .where(self.model.permission_group_id.in_(permission_group_ids))
            .options(joinedload(self.model.user))
        )

        if filters:
            filter_values = dict(filters.filter_values)
            functions_ops = filter_values.pop("functions", None)

            if functions_ops:
                for op, val in functions_ops.items():
                    names = val if isinstance(val, (list, tuple, set)) else [val]
                    subquery = select(
                        QualityControlFunction.quality_control_setting_id
                    ).where(QualityControlFunction.name.in_(names))
                    statement = statement.where(self.model.id.in_(subquery))

            if filter_values:
                statement = apply_filters(statement, filter_values)

        items = self.session.exec(statement).unique().all()
        return apply_sort_list(items, sort_by) if sort_by else items

    def create_allowed(
        self, payload, extra_data, permission_group_ids, ingest_type_info=None
    ):
        self.check_payload_permission_group(
            payload.permission_group_id, permission_group_ids
        )

        self.check_for_existing_name(payload.name, payload.permission_group_id)

        try:

            data = payload.model_dump(exclude={"quality_control_functions"})
            entity = QualityControlSetting.model_validate(data, update=extra_data)

            self.session.add(entity)
            self.session.flush()

            quality_control_setting_id_data = {"quality_control_setting_id": entity.id}

            for function_payload in payload.quality_control_functions:

                function_data = function_payload.model_dump(
                    exclude={"quality_control_function_arguments"}
                )
                db_function = QualityControlFunction.model_validate(
                    function_data, update=quality_control_setting_id_data
                )

                self.session.add(db_function)
                self.session.flush()

                quality_control_function_id_data = {
                    "quality_control_function_id": db_function.id
                }

                for (
                    function_argument_payload
                ) in function_payload.quality_control_function_arguments:
                    db_argument = QualityControlFunctionArgument.model_validate(
                        function_argument_payload,
                        update=quality_control_function_id_data,
                    )
                    self.session.add(db_argument)

            self.session.commit()
            self.session.refresh(entity)
            return entity
        except:
            self.session.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to create.")

    def update_allowed(
        self, id: int, payload, permission_group_ids, ingest_type_info=None
    ):
        try:
            update_payload = payload.model_dump(
                exclude_unset=True, exclude={"quality_control_functions"}
            )

            entity = self.find_allowed_one(id, permission_group_ids)

            if not entity:
                raise HTTPException(status_code=404, detail="Not found")

            if "name" in update_payload:
                self.check_for_existing_name_update(
                    update_payload["name"], entity.permission_group_id, entity.id
                )

            entity.sqlmodel_update(update_payload)
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)

            if payload.quality_control_functions is not None:
                try:
                    # Delete all existing functions + their arguments
                    statement = select(QualityControlFunction).where(
                        QualityControlFunction.quality_control_setting_id == id
                    )
                    existing_functions = self.session.exec(statement).all()
                    for func in existing_functions:
                        self.session.delete(func)

                    # Create new functions with arguments
                    for func_payload in payload.quality_control_functions:
                        func_data = func_payload.model_dump(
                            exclude={"quality_control_function_arguments"}
                        )
                        db_function = QualityControlFunction.model_validate(
                            func_data, update={"quality_control_setting_id": id}
                        )
                        self.session.add(db_function)
                        self.session.flush()

                        func_id_data = {"quality_control_function_id": db_function.id}
                        for arg_payload in (
                            func_payload.quality_control_function_arguments or []
                        ):
                            db_arg = QualityControlFunctionArgument.model_validate(
                                arg_payload.model_dump(),  # Converts Pydantic to dict
                                update=func_id_data,
                            )
                            self.session.add(db_arg)

                    self.session.commit()
                    self.session.refresh(entity)

                except Exception as e:
                    self.session.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to update quality control functions: {str(e)}",
                    )

            return entity
        except HTTPException as exception:
            raise exception
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")
