from typing import Type, TypeVar, Generic, List
from sqlmodel import Session, select, SQLModel, func
from fastapi import HTTPException
from .permission_group import PermissionGroup
from .database import Database
from utils import create_db_username, generate_password
from config import settings

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

    def find_all(self):
        statement = select(self.model)
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

    def find_allowed_all(self, permission_group_ids: list[int]) -> List[T]:
        statement = select(self.model).where(
            self.model.permission_group_id.in_(permission_group_ids)
        )
        return self.session.exec(statement).all()

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

    def create_allowed(self, payload, extra_data, permission_group_ids):
        self.check_payload_permission_group(
            payload.permission_group_id, permission_group_ids
        )

        self.check_for_existing_name(payload.name, payload.permission_group_id)

        try:
            entity = self.model.model_validate(payload, update=extra_data)
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to create.")

    def update_allowed(self, id: int, payload, permission_group_ids):
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
            return entity
        except HTTPException as exception:
            raise exception
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")

    def update_ingest_sftp(self, id: int, payload, permission_group_ids):

        # it is currently not allowed to update the permission group of an ingest sftp (s3store)
        # therefore the payload does not contain a permission_group_id , so we use an extra method
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
            return entity
        except HTTPException as exception:
            raise exception
        except Exception as e:
            print(str(e))
            self.session.rollback()
            raise HTTPException(status_code=400, detail="Failed to update.")

    def update_parser(self, id: int, data, permission_group_ids):
        print(f"data: {str(data)}")

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

    def find_allowed_all(self, permission_group_ids: list[int]) -> List[T]:
        statement = select(self.model).where(self.model.id.in_(permission_group_ids))
        return self.session.exec(statement).all()


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
            database.url = f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}"
            database.name = settings.POSTGRES_DB
            database.username = create_db_username(permission_group.name, False)
            database.read_only_username = create_db_username(
                permission_group.name, True
            )
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
