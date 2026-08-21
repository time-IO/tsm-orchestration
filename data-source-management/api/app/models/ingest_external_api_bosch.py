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


class IngestExternalApiBoschRead(IngestExternalApiRead):
    endpoint: str
    sensor_id: str
    bosch_username: str
    bosch_password: str
    period_in_minutes: int


class IngestExternalApiBoschCreate(IngestExternalApiCreate):
    endpoint: str
    sensor_id: str
    bosch_username: str
    bosch_password: str
    period_in_minutes: int


class IngestExternalApiBoschUpdate(IngestExternalApiUpdate):
    """Payload for a partial update of an Bosch‑type external‑API ingest.

    All fields are optional – you only have to send the ones you actually
    want to change.  Read‑only fields (id, uuid, created_at, ingest_type,
    api_type, permission_group) are intentionally omitted.
    """

    # ---- IngestExternalApiBosch fields ----
    endpoint: Optional[str] = None
    sensor_id: Optional[str] = None
    bosch_username: Optional[str] = None
    bosch_password: Optional[str] = None
    period_in_minutes: Optional[int] = None


class IngestExternalApiBosch(SQLModel, table=True):
    __tablename__ = "ingest_external_api_bosch"

    ingest_id: int = Field(
        foreign_key="ingest_external_api.ingest_id",
        primary_key=True,
        ondelete="CASCADE",
    )
    endpoint: str
    sensor_id: str
    bosch_username: str
    bosch_password: str = Field(
        sa_column=Column("bosch_password", EncryptedType, nullable=False)
    )
    period_in_minutes: int

    external_api: IngestExternalApi = Relationship(back_populates="bosch_detail")

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
