from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
import uuid as uuid_pkg
from datetime import datetime, timezone

from models import PermissionGroup


class IngestExternalApiTSystemsBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    description: str | None = None
    sync_enabled: bool = False
    group: str
    station_id: str
    tsystems_username: str
    tsystems_password: str


class IngestExternalApiTSystemsCreate(IngestExternalApiTSystemsBase):
    pass


class IngestExternalApiTSystemsUpdate(SQLModel):
    permission_group_id: int | None = None
    name: str | None = None
    description: str | None = None
    sync_enabled: bool | None = None
    group: str | None = None
    station_id: str | None = None
    tsystems_username: str | None = None
    tsystems_password: str | None = None


class IngestExternalApiTSystemsPublic(IngestExternalApiTSystemsBase):
    id: int
    uuid: uuid_pkg.UUID
    sync_interval_in_minutes: int
    created_by_id: int
    created_at: datetime
    permission_group: PermissionGroup


class IngestExternalApiTSystems(IngestExternalApiTSystemsBase, table=True):
    __tablename__ = "ingest_external_api_tsystems"

    __table_args__ = (
        UniqueConstraint(
            "name", "permission_group_id", name="tsystems_unique_name_permission_group"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    sync_interval_in_minutes: int = 60
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    permission_group: PermissionGroup = Relationship(
        back_populates="ingest_external_api_tsystems"
    )
