from sqlmodel import Field, SQLModel, Relationship, Index, func, column
import uuid as uuid_pkg
from datetime import datetime, timezone
from .permission_group import PermissionGroup
from pydantic import field_validator


class IngestExternalApiNeutronMonitorBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    description: str | None = None
    sync_interval_in_minutes: int | None = Field(nullable=True)
    sync_enabled: bool = False
    station_id: int = Field(foreign_key="neutron_monitor_station.id")
    time_resolution_in_minutes: int | None = Field(nullable=True, default=60)

    @field_validator("time_resolution_in_minutes")
    @classmethod
    def validate_time_resolution(cls, v: int | None) -> int:
        allowed = [None, 0, 2, 5, 10, 30, 60, 120, 360, 720, 1440, 39276, 525969]
        if v not in allowed:
            raise ValueError(
                f"time_resolution_in_minutes must be one of {allowed}, got {v}"
            )
        return v


class IngestExternalApiNeutronMonitorCreate(IngestExternalApiNeutronMonitorBase):
    pass


class IngestExternalApiNeutronMonitorUpdate(SQLModel):
    permission_group_id: int | None = None
    name: str | None = None
    description: str | None = None
    sync_interval_in_minutes: int | None = None
    sync_enabled: bool | None = None
    station_id: int | None = None
    time_resolution_in_minutes: int | None = None

    @field_validator("time_resolution_in_minutes")
    @classmethod
    def validate_time_resolution(cls, v: int | None) -> int:
        allowed = [None, 0, 2, 5, 10, 30, 60, 120, 360, 720, 1440, 39276, 525969]
        if v not in allowed:
            raise ValueError(
                f"time_resolution_in_minutes must be one of {allowed}, got {v}"
            )
        return v


class IngestExternalApiNeutronMonitorPublic(IngestExternalApiNeutronMonitorBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime
    permission_group: "PermissionGroup"
    station: "NeutronMonitorStation"


class IngestExternalApiNeutronMonitor(IngestExternalApiNeutronMonitorBase, table=True):
    __tablename__ = "ingest_external_api_neutron_monitor"

    __table_args__ = (
        Index(
            "ix_nm_name_permission_group",
            func.lower(column("name")),
            column("permission_group_id"),
            unique=True,
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    permission_group: "PermissionGroup" = Relationship(
        back_populates="ingest_external_api_neutron_monitor"
    )
    station: "NeutronMonitorStation" = Relationship(
        back_populates="ingest_external_api_neutron_monitor"
    )

    @property
    def mqtt_information(self) -> dict:
        return {
            "type": "nm",
            "version_id": 1,
            "enabled": self.sync_enabled,
            "sync_interval": self.sync_interval_in_minutes,
            "settings": {
                "station_id": self.station_id,
                "time_resolution": self.time_resolution_in_minutes,
            },
        }


from .neutron_monitor_station import NeutronMonitorStation
