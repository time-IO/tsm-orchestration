from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

from constants import ApiType
from .ingest_external_api import (
    IngestExternalApi,
    IngestExternalApiRead,
    IngestExternalApiCreate,
    IngestExternalApiUpdate,
)


class IngestExternalApiDwdRead(IngestExternalApiRead):
    station_id: str
    period_in_minutes: Optional[int]


class IngestExternalApiDwdCreate(IngestExternalApiCreate):
    station_id: str
    period_in_minutes: Optional[int] = None


class IngestExternalApiDwdUpdate(IngestExternalApiUpdate):
    station_id: Optional[str] = None
    period_in_minutes: Optional[int] = None


class IngestExternalApiDwd(SQLModel, table=True):
    __tablename__ = "ingest_external_api_dwd"

    ingest_id: int = Field(
        foreign_key="ingest_external_api.ingest_id",
        primary_key=True,
        ondelete="CASCADE",
    )
    station_id: str

    period_in_minutes: Optional[int] = None

    external_api: IngestExternalApi = Relationship(back_populates="dwd_detail")

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
