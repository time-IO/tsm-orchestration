from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
import uuid as uuid_pkg
from datetime import datetime, timezone

from models import PermissionGroup


class IngestExternalSftpBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    description: str | None = None
    uri: str
    path: str
    username: str
    password: str
    sync_interval_in_minutes: int
    sync_enabled: bool


class IngestExternalSftpCreate(IngestExternalSftpBase):
    pass


class IngestExternalSftpUpdate(SQLModel):
    permission_group_id: int | None = None
    name: str | None = None
    description: str | None = None
    uri: str | None = None
    path: str | None = None
    ext_sftp_user: str | None = None
    ext_sftp_password: str | None = None
    sync_interval_in_minutes: int | None = None
    sync_enabled: bool | None = None


class IngestExternalSftpPublic(IngestExternalSftpBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime
    ssh_private_key: str
    ssh_public_key: str
    permission_group: PermissionGroup


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
    ssh_private_key: str
    ssh_public_key: str

    permission_group: PermissionGroup = Relationship(
        back_populates="ingest_external_sftp"
    )
