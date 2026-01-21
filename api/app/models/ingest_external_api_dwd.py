from sqlmodel import Field, SQLModel
import uuid as uuid_pkg
from datetime import datetime, timezone


class IngestExternalApiDwdBase(SQLModel):
    project_id: int = Field(foreign_key="project.id")
    name: str
    description: str | None = None
    sync_enabled: bool = False
    station_id: str


class IngestExternalApiDwdCreate(IngestExternalApiDwdBase):
    pass


class IngestExternalApiDwdUpdate(SQLModel):
    project_id: int | None = None
    name: str | None = None
    description: str | None = None
    sync_enabled: bool | None = None
    station_id: str | None = None


class IngestExternalApiDwdPublic(IngestExternalApiDwdBase):
    id: int
    uuid: uuid_pkg.UUID
    sync_interval_in_minutes: int
    created_by_id: int
    created_at: datetime


class IngestExternalApiDwd(IngestExternalApiDwdBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    sync_interval_in_minutes: int = 1440
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
