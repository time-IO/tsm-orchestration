from sqlmodel import SQLModel, Field, CheckConstraint, Relationship
from typing import Optional
import uuid as uuid_pkg


class ParserRead(SQLModel):
    id: int
    parser_type: str
    uuid: uuid_pkg.UUID


class ParserCreate(SQLModel):
    pass


class ParserUpdate(SQLModel):
    pass


class Parser(SQLModel, table=True):
    __tablename__ = "parser"

    __table_args__ = (
        CheckConstraint(
            "parser_type IN ('csv','json','mqtt', 'soilcan')",
            name="ck_parser_type",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4, unique=True, index=True)
    parser_type: str = Field(
        description="type used for inheritance", index=True
    )  # e.g csv, json, mqtt
    ingest: Optional[list["Ingest"]] = Relationship(back_populates="parser")

    parser_mqtt_detail: Optional["ParserMqtt"] = Relationship(back_populates="parser")
    parser_detailed: Optional["ParserDetailed"] = Relationship(
        back_populates="parser", cascade_delete=True
    )

    @property
    def parser_info(self):

        child_info = None

        if self.parser_mqtt_detail is not None:
            child_info = self.parser_mqtt_detail.parser_info
        elif self.parser_detailed is not None:
            child_info = self.parser_detailed.parser_info

        infos = {"id": self.id, "parser_type": self.parser_type, **child_info}

        return infos
