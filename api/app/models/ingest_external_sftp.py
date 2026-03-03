from sqlalchemy import Column
from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
import uuid as uuid_pkg
from datetime import datetime, timezone
from .permission_group import PermissionGroup
from encryption import EncryptedType


class IngestExternalSftpBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    parser_csv_id: int = Field(foreign_key="parser_csv.id")
    name: str
    description: str | None = None
    uri: str
    path: str
    username: str | None = None
    password: str | None = None
    sync_interval_in_minutes: int | None = Field(ge=10, nullable=True)
    sync_enabled: bool = False
    filename_pattern: str


class IngestExternalSftpCreate(IngestExternalSftpBase):
    pass


class IngestExternalSftpUpdate(SQLModel):
    permission_group_id: int | None = None
    name: str | None = None
    description: str | None = None
    uri: str | None = None
    path: str | None = None
    username: str | None = None
    password: str | None = None
    sync_interval_in_minutes: int | None = Field(ge=10, default=None)
    sync_enabled: bool | None = None
    parser_csv_id: int | None = None
    filename_pattern: str | None = None


class IngestExternalSftpPublic(IngestExternalSftpBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime
    ssh_public_key: str
    permission_group: "PermissionGroup"
    parser_csv_id: int
    csv_parser: "CsvParser"


class IngestExternalSftp(IngestExternalSftpBase, table=True):
    __tablename__ = "ingest_external_sftp"

    __table_args__ = (
        UniqueConstraint(
            "name", "permission_group_id", name="ext_sftp_unique_name_permission_group"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ssh_private_key: str = Field(
        sa_column=Column("ssh_private_key", EncryptedType, nullable=True)
    )
    ssh_public_key: str
    password: str = Field(sa_column=Column("password", EncryptedType, nullable=True))

    permission_group: "PermissionGroup" = Relationship(
        back_populates="ingest_external_sftp"
    )
    csv_parser: "CsvParser" = Relationship(back_populates="ingest_external_sftp")


from .parser_csv import CsvParser
