from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional

from constants import ApiType
from .ingest_external_api import (
    IngestExternalApi,
    IngestExternalApiRead,
    IngestExternalApiCreate,
    IngestExternalApiUpdate,
)
from encryption import EncryptedType


class IngestExternalApiTheThingsNetworkRead(IngestExternalApiRead):
    api_key: str
    endpoint_uri: str


class IngestExternalApiTheThingsNetworkCreate(IngestExternalApiCreate):
    api_key: str
    endpoint_uri: str


class IngestExternalApiTheThingsNetworkUpdate(IngestExternalApiUpdate):
    api_key: Optional[str] = None
    endpoint_uri: Optional[str] = None


class IngestExternalApiTheThingsNetwork(SQLModel, table=True):
    __tablename__ = "ingest_external_api_the_things_network"

    ingest_id: int = Field(
        foreign_key="ingest_external_api.ingest_id",
        primary_key=True,
        ondelete="CASCADE",
    )

    api_key: str = Field(sa_column=Column("api_key", EncryptedType, nullable=False))
    endpoint_uri: str

    external_api: IngestExternalApi = Relationship(
        back_populates="the_things_network_detail"
    )

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
