from sqlmodel import Session
from models import ParserMqtt
from models.parser_mqtt import ParserMqttRead
from typing import Optional
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from fastapi import HTTPException

from models.filters import ParserMqttFilter
from fastapi_filters.ext.sqlalchemy import apply_filters


class ParserMqttRepository:
    def __init__(self, session: Session):
        self.model = ParserMqtt
        self.session = session

    def find_all(self, filters: Optional[ParserMqttFilter] = None):
        statement = (
            select(self.model)
            .join(self.model.parser)
            .options(joinedload(self.model.parser))
        )

        if filters:
            statement = apply_filters(statement, filters)

        results = self.session.exec(statement).unique().scalars().all()
        flatt_list = [self.to_flat(item) for item in results]
        return flatt_list

    def find_one(self, id: int):
        statement = (
            select(self.model)
            .where(self.model.parser_id == id)
            .options(joinedload(self.model.parser))
        )

        entity = self.session.exec(statement).unique().scalar_one_or_none()
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        return self.to_flat(entity)

    @staticmethod
    def to_flat(entity: ParserMqtt) -> ParserMqttRead:
        parser = entity.parser

        return ParserMqttRead(
            id=parser.id,
            uuid=parser.uuid,
            parser_type=parser.parser_type,
            name=entity.name,
        )
