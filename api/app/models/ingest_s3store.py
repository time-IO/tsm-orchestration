import uuid as uuid_pkg
from sqlmodel import Field, SQLModel, Relationship, Column, Index, func, column
from datetime import datetime, timezone

from .permission_group import PermissionGroup
from encryption import EncryptedType

# from .user import User # needs to be imported for relationship reasons otherwise an error is thrown during delete todo check this


class IngestS3StoreBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    parser_csv_id: int = Field(foreign_key="parser_csv.id")
    name: str
    description: str | None = None
    filename_pattern: str


class IngestS3StoreCreate(IngestS3StoreBase):
    pass


class IngestS3StoreUpdate(SQLModel):
    permission_group_id: int | None = None
    name: str | None = None
    description: str | None = None
    filename_pattern: str | None = None
    parser_csv_id: int | None = None


class IngestS3StorePublic(IngestS3StoreBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime
    permission_group: "PermissionGroup"
    username: str
    password: str
    bucket_name: str
    fileserver_uri: str
    parser_csv_id: int
    csv_parser: "CsvParser"


class IngestS3Store(IngestS3StoreBase, table=True):
    __tablename__ = "ingest_sftp"

    __table_args__ = (
        Index(
            "ix_s3store_name_permission_group",
            func.lower(column("name")),
            column("permission_group_id"),
            unique=True,
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    username: str
    password: str = Field(sa_column=Column("password", EncryptedType, nullable=False))
    bucket_name: str
    fileserver_uri: str

    permission_group: "PermissionGroup" = Relationship(back_populates="ingest_s3store")
    csv_parser: "CsvParser" = Relationship(back_populates="ingest_s3store")

    @property
    def mqtt_information(self) -> dict:
        from encryption import encryption_service

        return {
            "bucket_name": self.bucket_name,
            "username": self.username,
            "password": encryption_service.encrypt(self.password),
            "filename_pattern": self.filename_pattern,
        }


from .parser_csv import CsvParser
