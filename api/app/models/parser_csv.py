from sqlmodel import Field, SQLModel, Column, Relationship, UniqueConstraint
import uuid as uuid_pkg
from datetime import datetime, timezone
from sqlalchemy import JSON

from models import PermissionGroup

# ------------------- CsvParserTimestamp


class CsvParserTimestampColumnBase(SQLModel):
    csv_parser_id: int = Field(foreign_key="parser_csv.id", ondelete="CASCADE")
    column: int
    timestamp_format: str


class CsvParserTimestampColumnCreate(SQLModel):
    column: int
    timestamp_format: str


class CsvParserTimestampColumnUpdate(SQLModel):
    column: int | None = None
    timestamp_format: str | None = None


class CsvParserTimestampColumnPublic(SQLModel):
    id: int
    column: int
    timestamp_format: str


class CsvParserTimestampColumn(CsvParserTimestampColumnBase, table=True):
    __tablename__ = "parser_csv_timestamp_column"

    id: int | None = Field(default=None, primary_key=True)
    csv_parser: "CsvParser" = Relationship(back_populates="timestamp_columns")


# ------------------- CsvParser


class CsvParserBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    description: str | None = None
    delimiter: str
    headlines_to_exclude: int | None = None
    footlines_to_exclude: int | None = None
    pandas_read_csv: dict | None = Field(sa_column=Column(JSON), default_factory=dict)


class CsvParserCreate(CsvParserBase):
    timestamp_columns: list[CsvParserTimestampColumnCreate]


class CsvParserUpdate(SQLModel):
    # it should not __currently__ be possible to update the permission_group_id
    # it should not __currently__ be possible to send timestamp_columns (too complicated) instead use the routes to add and delete them to an existing csv_parser
    ## todo maybe i will test that with a special route + model
    name: str | None = None
    description: str | None = None
    delimiter: str | None = None
    headlines_to_exclude: int | None = None
    footlines_to_exclude: int | None = None
    pandas_read_csv: dict | None = None


class CsvParserPublic(CsvParserBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime
    timestamp_columns: list[CsvParserTimestampColumnPublic] = []
    permission_group: PermissionGroup


class CsvParser(CsvParserBase, table=True):
    __tablename__ = "parser_csv"

    __table_args__ = (
        UniqueConstraint(
            "name", "permission_group_id", name="csv_unique_name_permission_group"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timestamp_columns: list[CsvParserTimestampColumn] = Relationship(
        back_populates="csv_parser", cascade_delete=True
    )

    permission_group: PermissionGroup = Relationship(back_populates="csv_parser")
