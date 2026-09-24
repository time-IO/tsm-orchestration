from typing import Literal, Optional

from sqlmodel import SQLModel, Field, CheckConstraint, Relationship

from .parser_detailed import (
    ParserDetailed,
    ParserDetailedRead,
    ParserDetailedCreate,
    ParserDetailedUpdate,
)

SoilcanType = Literal["operating-parameters", "sensor-data", "weighing-data"]


class ParserSoilcanRead(ParserDetailedRead):
    type: str
    header: bool


class ParserSoilcanCreate(ParserDetailedCreate):
    type: SoilcanType
    header: bool


class ParserSoilcanUpdate(ParserDetailedUpdate):
    type: Optional[SoilcanType] = None
    header: Optional[bool] = None


class ParserSoilcan(SQLModel, table=True):
    __tablename__ = "parser_soilcan"

    __table_args__ = (
        CheckConstraint(
            "type IN ('operating-parameters','sensor-data','weighing-data')",
            name="ck_parser_soilcan_type",
        ),
    )

    parser_id: int = Field(
        foreign_key="parser_detailed.parser_id",
        primary_key=True,
        ondelete="CASCADE",
    )

    type: str = Field(index=True)
    header: bool

    parser_detailed: ParserDetailed = Relationship(back_populates="parser_soilcan")
