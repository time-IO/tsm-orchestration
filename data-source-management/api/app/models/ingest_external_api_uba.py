from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

from constants import ApiType
from .ingest_external_api import IngestExternalApi, IngestExternalApiRead
from .ingest import IngestCreate, IngestUpdate


class IngestExternalApiUbaRead(IngestExternalApiRead):
    station_id: str


class IngestExternalApiUbaCreate(IngestCreate):
    station_id: str
    sync_enabled: bool = False


class IngestExternalApiUbaUpdate(IngestUpdate):
    station_id: Optional[str] = None
    sync_enabled: Optional[bool] = None


class IngestExternalApiUba(SQLModel, table=True):
    __tablename__ = "ingest_external_api_uba"

    ingest_id: int = Field(
        foreign_key="ingest_external_api.ingest_id",
        primary_key=True,
        ondelete="CASCADE",
    )
    station_id: str

    external_api: IngestExternalApi = Relationship(back_populates="uba_detail")

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
