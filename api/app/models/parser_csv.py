from sqlmodel import Field, SQLModel, Column, Relationship, Index, func, column
import uuid as uuid_pkg
from datetime import datetime, timezone
from sqlalchemy import JSON


from .permission_group import PermissionGroup

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
    comment: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    header: int | None = None


class CsvParserCreate(CsvParserBase):
    timestamp_columns: list[CsvParserTimestampColumnCreate]


class CsvParserUpdate(SQLModel):
    # it should not __currently__ be possible to update the permission_group_id
    name: str | None = None
    description: str | None = None
    delimiter: str | None = None
    headlines_to_exclude: int | None = None
    footlines_to_exclude: int | None = None
    pandas_read_csv: dict | None = None
    timestamp_columns: list[CsvParserTimestampColumnUpdate] | None = None


class CsvParserPublic(CsvParserBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime
    timestamp_columns: list[CsvParserTimestampColumnPublic] = []
    permission_group: "PermissionGroup"


class CsvParser(CsvParserBase, table=True):
    __tablename__ = "parser_csv"

    __table_args__ = (
        Index(
            "ix_parser_csv_name_permission_group",
            func.lower(column("name")),
            column("permission_group_id"),
            unique=True,
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timestamp_columns: list[CsvParserTimestampColumn] = Relationship(
        back_populates="csv_parser", cascade_delete=True
    )

    permission_group: "PermissionGroup" = Relationship(back_populates="csv_parser")
    ingest_s3store: list["IngestS3Store"] = Relationship(back_populates="csv_parser")
    ingest_external_sftp: list["IngestExternalSftp"] = Relationship(
        back_populates="csv_parser"
    )

    @property
    def mqtt_information(self) -> dict:
        return {
            "default": 0,
            "parsers": [
                {
                    "type": "csvparser",
                    "name": self.name,
                    "settings": {
                        "delimiter": self.delimiter,
                        "skipfooter": self.footlines_to_exclude,
                        "skiprows": self.headlines_to_exclude,
                        "header": self.header,
                        "comment": self.comment,
                        "pandas_read_csv": self.pandas_read_csv,
                        "timestamp_columns": [
                            {
                                "column": tc.column,
                                "timestamp_format": tc.timestamp_format,
                            }
                            for tc in self.timestamp_columns
                        ],
                    },
                }
            ],
        }


from .ingest_s3store import IngestS3Store
from .ingest_external_sftp import IngestExternalSftp
