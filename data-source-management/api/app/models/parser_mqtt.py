from sqlmodel import SQLModel, Field, Relationship
from .parser import Parser, ParserRead


class ParserMqttRead(ParserRead):
    name: str


class ParserMqtt(SQLModel, table=True):
    __tablename__ = "parser_mqtt"

    parser_id: int = Field(foreign_key="parser.id", primary_key=True)
    name: str

    parser: Parser = Relationship(back_populates="parser_mqtt_detail")

    @property
    def parser_info(self):
        return {"name": self.name}
