from typing import Type, TypeVar, Generic, List
from sqlmodel import Session, select, SQLModel
from fastapi import HTTPException

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

    def create_allowed(self, payload, extra_data, permission_group_ids):
        self.__check_payload_permission_group(payload, permission_group_ids)
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

        self.__check_payload_permission_group(payload, permission_group_ids)

        if payload.permission_group_id not in permission_group_ids:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: user does not belong to that permission group.",
            )
        try:
            entity = self.find_allowed_one(id, permission_group_ids)

            if not entity:
                raise HTTPException(status_code=404, detail="Not found")

            data = payload.model_dump(exclude_unset=True)
            entity.sqlmodel_update(data)
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
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
    def __check_payload_permission_group(payload, permission_group_ids):
        if payload.permission_group_id not in permission_group_ids:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: user does not belong to that permission group.",
            )
