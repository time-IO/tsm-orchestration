from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
import pytz
from pydantic import field_validator

from .parser_detailed import (
    ParserDetailed,
    ParserDetailedRead,
    ParserDetailedCreate,
    ParserDetailedUpdate,
)


class ParserJsonTimestampKeyPublic(SQLModel):
    id: int
    key: str
    format: str


class ParserJsonRead(ParserDetailedRead):
    comment: Optional[str] = None
    timestamp_keys: list[ParserJsonTimestampKeyPublic] = []
    timezone: Optional[str] = None


class ParserJsonTimestampKeyCreate(SQLModel):
    key: str
    format: str


class ParserJsonCreate(ParserDetailedCreate):
    comment: Optional[str] = None
    timestamp_keys: list[ParserJsonTimestampKeyCreate]
    timezone: str


class ParserJsonTimestampKeyUpdate(ParserJsonTimestampKeyCreate):
    pass


class ParserJsonUpdate(ParserDetailedUpdate):
    comment: Optional[str] = None
    timestamp_keys: Optional[list[ParserJsonTimestampKeyUpdate]] = None
    timezone: Optional[str] = None


class ParserJson(SQLModel, table=True):
    __tablename__ = "parser_json"

    parser_id: int = Field(
        foreign_key="parser_detailed.parser_id",
        primary_key=True,
        ondelete="CASCADE",
    )

    comment: Optional[str] = None
    timezone: Optional[str] = None
    timestamp_keys: list["ParserJsonTimestampKey"] = Relationship(
        back_populates="parser_json", cascade_delete=True
    )

    parser_detailed: ParserDetailed = Relationship(back_populates="parser_json")


class ParserJsonTimestampKey(SQLModel, table=True):
    __tablename__ = "parser_json_timestamp_key"

    id: int | None = Field(default=None, primary_key=True)
    parser_json_id: int = Field(foreign_key="parser_json.parser_id", ondelete="CASCADE")
    key: str
    format: str

    parser_json: "ParserJson" = Relationship(back_populates="timestamp_keys")

    # @field_validator("timezone")
    # @classmethod
    # def validate_timezone(cls, value: any) -> str:
    #     if value not in pytz.all_timezones:
    #         raise ValueError(f"{value} is not a valid timezone")
    #     return value
    #
    #
