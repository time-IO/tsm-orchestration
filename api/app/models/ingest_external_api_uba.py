from sqlmodel import Field, SQLModel, Relationship
import uuid as uuid_pkg
from datetime import datetime, timezone


class IngestExternalApiUbaBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    station_id: str
    description: str | None = None
    sync_enabled: bool = False


class IngestExternalApiUbaCreate(IngestExternalApiUbaBase):
    pass


class IngestExternalApiUbaUpdate(SQLModel):
    permission_group_id: int | None
    name: str | None
    station_id: str | None
    description: str | None
    sync_enabled: bool | None


class IngestExternalApiUbaPublic(IngestExternalApiUbaBase):
    id: int
    uuid: uuid_pkg.UUID
    sync_interval_in_minutes: int
    created_by_id: int
    created_at: datetime
    permission_group: "PermissionGroup"


class IngestExternalApiUba(IngestExternalApiUbaBase, table=True):
    __tablename__ = "ingest_external_api_uba"

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    sync_interval_in_minutes: int = 60
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    permission_group: "PermissionGroup" = Relationship(back_populates="ingest_external_api_uba")

# fix to avoid circular imports
from .permission_group import PermissionGroup
IngestExternalApiUba.model_rebuild()