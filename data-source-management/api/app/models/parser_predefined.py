from sqlmodel import SQLModel, Field, Relationship
from .parser import Parser, ParserRead


class ParserPredefinedRead(ParserRead):
    name: str


class ParserPredefined(SQLModel, table=True):
    __tablename__ = "parser_predefined"

    parser_id: int = Field(foreign_key="parser.id", primary_key=True)
    # Stable implementation key used by timeio.parser.get_parser.
    name: str

    parser: Parser = Relationship(back_populates="parser_predefined")

    @property
    def parser_info(self):
        return {"name": self.name}
