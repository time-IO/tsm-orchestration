from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, Literal
from enum import Enum

from constants import ApiType
from .ingest_external_api import (
    IngestExternalApi,
    IngestExternalApiRead,
    IngestExternalApiCreate,
    IngestExternalApiUpdate,
)
from encryption import EncryptedType


class UnitsEnum(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"


class IngestExternalApiZentraRead(IngestExternalApiRead):
    device_sn: str
    period_in_minutes: int
    units: Optional[Literal["metric", "imperial"]] = "metric"
    api_key: str


class IngestExternalApiZentraCreate(IngestExternalApiCreate):
    device_sn: str
    period_in_minutes: int
    units: Optional[Literal["metric", "imperial"]] = "metric"
    api_key: str


class IngestExternalApiZentraUpdate(IngestExternalApiUpdate):
    period_in_minutes: Optional[int] = None
    units: Optional[Literal["metric", "imperial"]] = None
    api_key: Optional[str] = None


class IngestExternalApiZentra(SQLModel, table=True):
    __tablename__ = "ingest_external_api_zentra"

    ingest_id: int = Field(
        foreign_key="ingest_external_api.ingest_id",
        primary_key=True,
        ondelete="CASCADE",
    )
    device_sn: str
    period_in_minutes: int
    units: Optional[UnitsEnum] = UnitsEnum.METRIC
    api_key: str = Field(sa_column=Column("api_key", EncryptedType, nullable=False))
    external_api: IngestExternalApi = Relationship(back_populates="zentra_detail")

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
