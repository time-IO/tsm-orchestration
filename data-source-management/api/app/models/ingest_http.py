from sqlmodel import SQLModel, Field, Relationship, Column, Index
from typing import Optional
from encryption import EncryptedType
from .ingest import Ingest, IngestRead, IngestCreate, IngestUpdate

# Sent as the X-Api-Key header to authenticate incoming HTTP ingest requests.
API_KEY_MIN_LENGTH = 8


class IngestHttpRead(IngestRead):
    path_for_posts: Optional[str] = None
    file_type: str
    api_key: str
    enabled: bool
    bucket_name: str
    bucket_username: str
    bucket_password: str


class IngestHttpCreate(IngestCreate):
    path_for_posts: Optional[str] = None
    file_type: str
    api_key: str = Field(min_length=API_KEY_MIN_LENGTH)
    enabled: bool = False


class IngestHttpUpdate(IngestUpdate):
    path_for_posts: Optional[str] = None
    file_type: Optional[str] = None
    api_key: Optional[str] = Field(default=None, min_length=API_KEY_MIN_LENGTH)
    enabled: Optional[bool] = None


class IngestHttp(SQLModel, table=True):
    __tablename__ = "ingest_http"
    __table_args__ = (
        # path_for_posts feeds the global Bento HTTP route (/http-ingest/{path}),
        # so it must be unique instance-wide. NULL is excluded since
        # setup_bento.py falls back to the (already unique) thing UUID then.
        Index(
            "ix_ingest_http_path_for_posts",
            "path_for_posts",
            unique=True,
            postgresql_where=Column("path_for_posts").isnot(None),
        ),
    )

    ingest_id: int = Field(
        foreign_key="ingest.id", primary_key=True, ondelete="CASCADE"
    )

    path_for_posts: Optional[str] = None
    file_type: str
    api_key: str = Field(
        min_length=API_KEY_MIN_LENGTH,
        sa_column=Column("api_key", EncryptedType, nullable=False),
    )
    enabled: bool = False

    bucket_name: str
    bucket_username: str
    bucket_password: str = Field(
        sa_column=Column("bucket_password", EncryptedType, nullable=False)
    )

    ingest: Ingest = Relationship(back_populates="http_detail")

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
