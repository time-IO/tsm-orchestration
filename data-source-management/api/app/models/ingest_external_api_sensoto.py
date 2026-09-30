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


class IngestExternalApiSensotoRead(IngestExternalApiRead):
    network: str
    device: str
    organization: str
    period_in_minutes: int
    token: Optional[str] = None


class IngestExternalApiSensotoCreate(IngestExternalApiCreate):
    network: str
    device: str
    organization: str = "open"
    period_in_minutes: int
    token: Optional[str] = None


class IngestExternalApiSensotoUpdate(IngestExternalApiUpdate):
    network: Optional[str] = None
    device: Optional[str] = None
    organization: Optional[str] = None
    period_in_minutes: Optional[int] = None
    token: Optional[str] = None


class IngestExternalApiSensoto(SQLModel, table=True):
    __tablename__ = "ingest_external_api_sensoto"

    ingest_id: int = Field(
        foreign_key="ingest_external_api.ingest_id",
        primary_key=True,
        ondelete="CASCADE",
    )
    network: str = Field(nullable=False)
    device: str = Field(nullable=False)
    organization: str = Field(default="open", nullable=False)
    period_in_minutes: int = Field(nullable=False)
    token: Optional[str] = Field(
        default=None, sa_column=Column("token", EncryptedType, nullable=True)
    )

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
