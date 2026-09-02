from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

from constants import ApiType
from .ingest_external_api import (
    IngestExternalApi,
    IngestExternalApiRead,
    IngestExternalApiCreate,
    IngestExternalApiUpdate,
)
from pydantic import field_validator


class IngestExternalApiNeutronMonitorRead(IngestExternalApiRead):
    station_id: int
    time_resolution_in_minutes: Optional[int]
    station: "NeutronMonitorStation"


class IngestExternalApiNeutronMonitorCreate(IngestExternalApiCreate):
    station_id: int
    time_resolution_in_minutes: Optional[int]


class IngestExternalApiNeutronMonitorUpdate(IngestExternalApiUpdate):
    station_id: Optional[int] = None
    time_resolution_in_minutes: Optional[int] = None


class IngestExternalApiNeutronMonitor(SQLModel, table=True):
    __tablename__ = "ingest_external_api_neutron_monitor"

    ingest_id: int = Field(
        foreign_key="ingest_external_api.ingest_id",
        primary_key=True,
        ondelete="CASCADE",
    )
    station_id: int = Field(foreign_key="neutron_monitor_station.id")
    time_resolution_in_minutes: Optional[int] = Field(nullable=True, default=60)

    external_api: IngestExternalApi = Relationship(
        back_populates="neutron_monitor_detail"
    )

    station: "NeutronMonitorStation" = Relationship(
        back_populates="ingest_external_api_neutron_monitor"
    )

    @field_validator("time_resolution_in_minutes")
    @classmethod
    def validate_time_resolution(cls, v: Optional[int]) -> int:
        allowed = [None, 0, 2, 5, 10, 30, 60, 120, 360, 720, 1440, 39276, 525969]
        if v not in allowed:
            raise ValueError(
                f"time_resolution_in_minutes must be one of {allowed}, got {v}"
            )
        return v

    @property
    def ingest_type(self):
        return self.external_api.ingest.ingest_type

    @property
    def permission_group(self):
        return self.external_api.ingest.permission_group

    @property
    def uuid(self):
        return self.external_api.ingest.uuid

    @property
    def name(self):
        return self.external_api.ingest.name

    @property
    def description(self):
        return self.external_api.ingest.description


from .neutron_monitor_station import NeutronMonitorStation
