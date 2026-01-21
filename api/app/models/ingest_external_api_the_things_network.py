from sqlmodel import Field, SQLModel
import uuid as uuid_pkg
from datetime import datetime, timezone


class IngestExternalApiTheThingsNetworkBase(SQLModel):
    project_id: int = Field(foreign_key="project.id")
    name: str
    description: str | None = None
    sync_interval_in_minutes: int
    sync_enabled: bool = False
    api_key: str
    endpoint_uri: str


class IngestExternalApiTheThingsNetworkCreate(IngestExternalApiTheThingsNetworkBase):
    pass


class IngestExternalApiTheThingsNetworkUpdate(SQLModel):
    project_id: int | None = None
    name: str | None = None
    description: str | None = None
    sync_interval_in_minutes: int | None = None
    sync_enabled: bool | None = None
    api_key: str | None = None
    endpoint_uri: str | None = None


class IngestExternalApiTheThingsNetworkPublic(IngestExternalApiTheThingsNetworkBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime


class IngestExternalApiTheThingsNetwork(IngestExternalApiTheThingsNetworkBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
