from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

from constants import ApiType
from .ingest_external_api import (
    IngestExternalApi,
    IngestExternalApiRead,
    IngestExternalApiCreate,
    IngestExternalApiUpdate,
)


class IngestExternalApiSensotoRead(IngestExternalApiRead):
    network: str
    device: str


class IngestExternalApiSensotoCreate(IngestExternalApiCreate):
    network: str
    device: str


class IngestExternalApiSensotoUpdate(IngestExternalApiUpdate):
    network: Optional[str] = None
    device: Optional[str] = None


class IngestExternalApiSensoto(SQLModel, table=True):
    __tablename__ = "ingest_external_api_sensoto"

    ingest_id: int = Field(
        foreign_key="ingest_external_api.ingest_id",
        primary_key=True,
        ondelete="CASCADE",
    )
    network: str = Field(nullable=False)
    device: str = Field(nullable=False)

    external_api: IngestExternalApi = Relationship(back_populates="sensoto")

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
