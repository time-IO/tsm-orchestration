from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional

from .ingest_external_api import (
    IngestExternalApi,
    IngestExternalApiRead,
    IngestExternalApiCreate,
    IngestExternalApiUpdate,
)
from encryption import EncryptedType


class IngestExternalApiMyAtmosphereRead(IngestExternalApiRead):
    customer_id: int
    serial_number: str
    period_in_minutes: int
    api_key: str


class IngestExternalApiMyAtmosphereCreate(IngestExternalApiCreate):
    customer_id: int = Field(gt=0)
    serial_number: str = Field(min_length=1)
    period_in_minutes: int = Field(gt=0)
    api_key: str = Field(min_length=1)


class IngestExternalApiMyAtmosphereUpdate(IngestExternalApiUpdate):
    customer_id: Optional[int] = Field(default=None, gt=0)
    serial_number: Optional[str] = Field(default=None, min_length=1)
    period_in_minutes: Optional[int] = Field(default=None, gt=0)
    api_key: Optional[str] = Field(default=None, min_length=1)


class IngestExternalApiMyAtmosphere(SQLModel, table=True):
    __tablename__ = "ingest_external_api_myatmosphere"

    ingest_id: int = Field(
        foreign_key="ingest_external_api.ingest_id",
        primary_key=True,
        ondelete="CASCADE",
    )
    customer_id: int
    serial_number: str
    period_in_minutes: int
    api_key: str = Field(sa_column=Column("api_key", EncryptedType, nullable=False))
    external_api: IngestExternalApi = Relationship(back_populates="myatmosphere_detail")

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
