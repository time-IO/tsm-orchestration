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
            "parser_type IN ('csv','json','predefined', 'soilcan')",
            name="ck_parser_type",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4, unique=True, index=True)
    parser_type: str = Field(
        description="type used for inheritance", index=True
    )  # e.g csv, json, predefined
    ingest: Optional[list["Ingest"]] = Relationship(back_populates="parser")

    # Predefined parsers share fixed implementations and have no user-editable
    # configuration. Their names are implementation keys, independent of transport.
    parser_predefined: Optional["ParserPredefined"] = Relationship(
        back_populates="parser"
    )
    # User-managed CSV, JSON and Soilcan parsers share metadata here and link
    # through ParserDetailed to their subtype-specific settings.
    parser_detailed: Optional["ParserDetailed"] = Relationship(
        back_populates="parser", cascade_delete=True
    )

    @property
    def parser_info(self):

        child_info = None

        if self.parser_predefined is not None:
            child_info = self.parser_predefined.parser_info
        elif self.parser_detailed is not None:
            child_info = self.parser_detailed.parser_info

        infos = {"id": self.id, "parser_type": self.parser_type, **child_info}

        return infos


class ParsedDataResponse(SQLModel):
    data: list[dict]
    error: str
    is_valid: bool
    warnings: list[str]
