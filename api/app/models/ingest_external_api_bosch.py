from sqlmodel import Field, SQLModel
import uuid as uuid_pkg
from datetime import datetime, timezone


class IngestExternalApiBoschBase(SQLModel):
    project_id: int = Field(foreign_key="project.id")
    name: str
    description: str | None = None
    sync_interval_in_minutes: int
    sync_enabled: bool
    endpoint: str
    sensor_id: str
    bosch_username: str
    bosch_password: str
    period_in_minutes: int


class IngestExternalApiBoschCreate(IngestExternalApiBoschBase):
    pass


class IngestExternalApiBoschUpdate(SQLModel):
    project_id: int | None = None
    name: str | None = None
    description: str | None = None
    sync_interval_in_minutes: int | None = None
    sync_enabled: bool | None = None
    endpoint: str | None = None
    sensor_id: str | None = None
    username: str | None = None
    password: str | None = None
    period_in_minutes: int | None = None


class IngestExternalApiBoschPublic(IngestExternalApiBoschBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime


class IngestExternalApiBosch(IngestExternalApiBoschBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
