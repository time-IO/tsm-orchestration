from sqlmodel import Field, SQLModel, Column, Relationship
import uuid as uuid_pkg
from datetime import datetime, timezone
from sqlalchemy import JSON
from .user import User # needs to be imported for relationship reasons otherwise an error is thrown during delete todo check this

# ------------------- CsvParserTimestamp

class CsvParserTimestampColumnBase(SQLModel):
    csv_parser_id: int = Field(foreign_key="csvparser.id", ondelete="CASCADE")
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
    id: int | None = Field(default=None, primary_key=True)
    csv_parser: "CsvParser" = Relationship(back_populates="timestamp_columns")

# ------------------- CsvParser

class CsvParserBase(SQLModel):
    project_id: int = Field(foreign_key="project.id")
    name: str
    description: str | None = None
    delimiter: str
    headlines_to_exclude: int | None = None
    footlines_to_exclude: int | None = None
    pandas_read_csv: dict | None = Field(sa_column=Column(JSON), default_factory=dict)

class CsvParserCreate(CsvParserBase):
    timestamp_columns: list[CsvParserTimestampColumnCreate]

class CsvParserUpdate(SQLModel):
    # it should not __currently__ be possible to update the project_id
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

class CsvParser(CsvParserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timestamp_columns: list[CsvParserTimestampColumn] = Relationship(back_populates="csv_parser", cascade_delete=True)