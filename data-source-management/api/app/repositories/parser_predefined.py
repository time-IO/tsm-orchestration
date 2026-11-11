from sqlmodel import Session
from models import ParserPredefined
from models.parser_predefined import ParserPredefinedRead
from typing import Optional
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from fastapi import HTTPException

from models.filters.parser_predefined import ParserPredefinedFilter
from timeio.parser.predefined import PREDEFINED_PARSER_RECOMMENDATIONS
from fastapi_filters.ext.sqlalchemy import apply_filters


class ParserPredefinedRepository:
    def __init__(self, session: Session, recommended_for: str | None = None):
        self.model = ParserPredefined
        self.session = session
        self.recommended_for = recommended_for

    def find_all(self, filters: Optional[ParserPredefinedFilter] = None):
        statement = (
            select(self.model)
            .join(self.model.parser)
            .options(joinedload(self.model.parser))
        )

        if self.recommended_for:
            statement = statement.where(
                self.model.name.in_(
                    PREDEFINED_PARSER_RECOMMENDATIONS[self.recommended_for]
                )
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

        if self.recommended_for:
            statement = statement.where(
                self.model.name.in_(
                    PREDEFINED_PARSER_RECOMMENDATIONS[self.recommended_for]
                )
            )
        entity = self.session.exec(statement).unique().scalar_one_or_none()
        if not entity:
            raise HTTPException(status_code=404, detail="Not found")
        return self.to_flat(entity)

    @staticmethod
    def to_flat(entity: ParserPredefined) -> ParserPredefinedRead:
        parser = entity.parser

        return ParserPredefinedRead(
            id=parser.id,
            uuid=parser.uuid,
            parser_type=parser.parser_type,
            name=entity.name,
        )
