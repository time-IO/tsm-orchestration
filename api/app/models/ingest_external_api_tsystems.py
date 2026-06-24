from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional

from constants import ApiType
from .ingest_external_api import IngestExternalApi, IngestExternalApiRead
from .ingest import IngestCreate, IngestUpdate
from encryption import EncryptedType


class IngestExternalApiTSystemsRead(IngestExternalApiRead):
    group: str
    station_id: str
    tsystems_username: str
    tsystems_password: str


class IngestExternalApiTSystemsCreate(IngestCreate):
    sync_enabled: bool = False
    group: str
    station_id: str
    tsystems_username: str
    tsystems_password: str


class IngestExternalApiTSystemsUpdate(IngestUpdate):
    sync_enabled: Optional[bool] = None
    group: Optional[str] = None
    station_id: Optional[str] = None
    tsystems_username: Optional[str] = None
    tsystems_password: Optional[str] = None


class IngestExternalApiTSystems(SQLModel, table=True):
    __tablename__ = "ingest_external_api_tsystems"

    ingest_id: int = Field(
        foreign_key="ingest_external_api.ingest_id",
        primary_key=True,
        ondelete="CASCADE",
    )

    group: str
    station_id: str
    tsystems_username: str

    tsystems_password: str = Field(
        sa_column=Column("tsystems_password", EncryptedType, nullable=False)
    )

    external_api: IngestExternalApi = Relationship(back_populates="tsystems_detail")

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
