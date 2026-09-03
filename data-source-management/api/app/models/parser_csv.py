import json

from pydantic import field_validator
from sqlmodel import SQLModel, Field, Column, Relationship
from typing import Optional, Any
from sqlalchemy import JSON
import pytz

from utils import valid_codecs

from .parser_detailed import (
    ParserDetailed,
    ParserDetailedRead,
    ParserDetailedCreate,
    ParserDetailedUpdate,
)


class ParserCsvTimestampColumnPublic(SQLModel):
    id: int
    column: int
    timestamp_format: str


class ParserCsvRead(ParserDetailedRead):
    timestamp_columns: list[ParserCsvTimestampColumnPublic] = []
    delimiter: str
    timezone: Optional[str] = None
    encoding: Optional[str] = None
    headlines_to_exclude: Optional[str] = None
    footlines_to_exclude: Optional[int] = None
    pandas_read_csv: Optional[dict] = Field(
        sa_column=Column(JSON), default_factory=dict
    )
    comment: Optional[list[str]] = Field(sa_column=Column(JSON), default_factory=list)
    header: Optional[int] = None


class ParserCsvTimestampColumnCreate(SQLModel):
    column: int
    timestamp_format: str


class ParserCsvCreate(ParserDetailedCreate):
    delimiter: str
    timezone: str
    encoding: str
    headlines_to_exclude: Optional[str] = None
    footlines_to_exclude: Optional[int] = None
    pandas_read_csv: Optional[dict] = None
    comment: Optional[list[str]] = None
    header: Optional[int] = None
    timestamp_columns: list[ParserCsvTimestampColumnCreate]


class ParserCsvTimestampColumnUpdate(ParserCsvTimestampColumnCreate):
    pass


class ParserCsvUpdate(ParserDetailedUpdate):
    delimiter: Optional[str] = None
    timezone: Optional[str] = None
    encoding: Optional[str] = None
    headlines_to_exclude: Optional[str] = None
    footlines_to_exclude: Optional[int] = None
    pandas_read_csv: Optional[dict] = None
    comment: Optional[list[str]] = None
    header: Optional[int] = None
    timestamp_columns: Optional[list[ParserCsvTimestampColumnUpdate]] = None


class ParserCsvParse(ParserCsvUpdate):
    pass


class ParserCsv(SQLModel, table=True):
    __tablename__ = "parser_csv"

    parser_id: int = Field(
        foreign_key="parser_detailed.parser_id",
        primary_key=True,
        ondelete="CASCADE",
    )
    delimiter: str
    timezone: Optional[str] = None
    encoding: Optional[str] = None
    headlines_to_exclude: Optional[str] = None
    footlines_to_exclude: Optional[int] = None
    pandas_read_csv: Optional[dict] = Field(
        sa_column=Column(JSON), default_factory=dict
    )
    comment: Optional[list[str]] = Field(sa_column=Column(JSON), default_factory=list)
    header: Optional[int] = None

    timestamp_columns: list["ParserCsvTimestampColumn"] = Relationship(
        back_populates="parser_csv", cascade_delete=True
    )

    # Relationships
    parser_detailed: ParserDetailed = Relationship(back_populates="parser_csv")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Any) -> str:
        if value not in pytz.all_timezones:
            raise ValueError(f"{value} is not a valid timezone")
        return value

    @field_validator("encoding")
    @classmethod
    def validate_encoding(cls, value: Any) -> str:
        if value not in valid_codecs:
            raise ValueError(f"{value} is not a valid encoding")
        return value


class ParserCsvTimestampColumn(SQLModel, table=True):
    __tablename__ = "parser_csv_timestamp_column"

    parser_csv_id: int = Field(foreign_key="parser_csv.parser_id", ondelete="CASCADE")

    id: int | None = Field(default=None, primary_key=True)
    column: int
    timestamp_format: str

    parser_csv: "ParserCsv" = Relationship(back_populates="timestamp_columns")
