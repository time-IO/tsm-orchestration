from sqlmodel import Field, SQLModel
import uuid as uuid_pkg
from datetime import datetime, timezone
from .neutron_monitor_stations import NeutronMonitorStations

class IngestExternalApiNeutronMonitorBase(SQLModel):
    project_id: int = Field(foreign_key="project.id")
    name: str
    description: str | None = None
    sync_interval_in_minutes: int
    sync_enabled: bool = False
    station_id: int = Field(foreign_key="neutron_monitor_stations.id")


class IngestExternalApiNeutronMonitorCreate(IngestExternalApiNeutronMonitorBase):
    pass


class IngestExternalApiNeutronMonitorUpdate(SQLModel):
    project_id: int | None = None
    name: str | None = None
    description: str | None = None
    sync_interval_in_minutes: int | None = None
    sync_enabled: bool | None = None
    station_id: int | None = None


class IngestExternalApiNeutronMonitorPublic(IngestExternalApiNeutronMonitorBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime


class IngestExternalApiNeutronMonitor(IngestExternalApiNeutronMonitorBase, table=True):
    __tablename__ = "ingest_external_api_neutron_monitor"

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
