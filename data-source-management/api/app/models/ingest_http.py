from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional
from encryption import EncryptedType
from .ingest import Ingest, IngestRead, IngestCreate, IngestUpdate


class IngestHttpRead(IngestRead):
    path_for_posts: str
    file_type: str
    api_key: str
    enabled: bool


class IngestHttpCreate(IngestCreate):
    path_for_posts: Optional[str] = None
    file_type: str
    api_key: str
    enabled: bool = False


class IngestHttpUpdate(IngestUpdate):
    path_for_posts: Optional[str] = None
    file_type: Optional[str] = None
    api_key: Optional[str] = None
    enabled: Optional[bool] = None


class IngestHttp(SQLModel, table=True):
    __tablename__ = "ingest_http"

    ingest_id: int = Field(
        foreign_key="ingest.id", primary_key=True, ondelete="CASCADE"
    )

    path_for_posts: Optional[str] = None
    file_type: str
    api_key: str = Field(sa_column=Column("api_key", EncryptedType, nullable=False))
    enabled: bool = False

    ingest: Ingest = Relationship(back_populates="ingest_http_detail")

    @property
    def ingest_type(self):
        return self.ingest.ingest_type

    @property
    def permission_group(self):
        return self.ingest.permission_group

    @property
    def uuid(self):
        return self.ingest.uuid

    @property
    def name(self):
        return self.ingest.name

    @property
    def description(self):
        return self.ingest.description
