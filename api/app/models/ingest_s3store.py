import uuid as uuid_pkg
from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
from datetime import datetime, timezone
from .permission_group import PermissionGroup

# from .user import User # needs to be imported for relationship reasons otherwise an error is thrown during delete todo check this


class IngestS3StoreBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    description: str | None = None
    filename_pattern: str


class IngestS3StoreCreate(IngestS3StoreBase):
    pass


class IngestS3StoreUpdate(SQLModel):
    permission_group_id: int | None = None
    name: str | None = None
    description: str | None = None
    filename_pattern: str | None = None


class IngestS3StorePublic(IngestS3StoreBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime
    permission_group: "PermissionGroup"


class IngestS3Store(IngestS3StoreBase, table=True):
    __tablename__ = "ingest_s3store"

    __table_args__ = (
        UniqueConstraint(
            "name", "permission_group_id", name="s3store_unique_name_permission_group"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    username: str
    password: str
    bucket_name: str

    permission_group: "PermissionGroup" = Relationship(back_populates="ingest_s3store")
