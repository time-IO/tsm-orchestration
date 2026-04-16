from sqlmodel import Field, SQLModel, Relationship, Column, Index, func, column
import uuid as uuid_pkg
from datetime import datetime, timezone
from utils import get_ssh_priv_key
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
        Index(
            "ix_ext_sftp_name_permission_group",
            func.lower(column("name")),
            column("permission_group_id"),
            unique=True,
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
    bucket_name: str
    bucket_username: str
    bucket_password: str = Field(
        sa_column=Column("bucket_password", EncryptedType, nullable=False)
    )

    permission_group: "PermissionGroup" = Relationship(
        back_populates="ingest_external_sftp"
    )
    csv_parser: "CsvParser" = Relationship(back_populates="ingest_external_sftp")

    @property
    def mqtt_information(self):
        from encryption import encryption_service

        return {
            "sync_enabled": self.sync_enabled,
            "uri": self.uri,
            "path": self.path,
            "username": self.username,
            "password": encryption_service.encrypt(self.password),
            "sync_interval": self.sync_interval_in_minutes,
            "public_key": self.ssh_public_key,
            "private_key": encryption_service.encrypt(self.ssh_private_key),
        }

    @property
    def mqtt_rawdatastorage(self):
        from encryption import encryption_service

        return {
            "bucket_name": self.bucket_name,
            "username": self.bucket_username,
            "password": encryption_service.encrypt(self.bucket_password),
            "filename_pattern": self.filename_pattern,
        }


from .parser_csv import CsvParser
