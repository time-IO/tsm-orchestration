from sqlmodel import SQLModel, Field, Index, func, Column, CheckConstraint, Relationship
import uuid as uuid_pkg
from datetime import datetime, timezone
from typing import Optional
from .permission_group import PermissionGroup
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class IngestRead(SQLModel):
    id: int
    uuid: uuid_pkg.UUID
    created_at: Optional[datetime]
    ingest_type: str
    name: str
    permission_group_id: int
    description: Optional[str]
    created_by_id: Optional[int]
    parser_id: Optional[int]

    permission_group: dict


class IngestWithApiInfoRead(SQLModel):
    id: int
    uuid: uuid_pkg.UUID
    created_at: Optional[datetime]
    ingest_type: str
    name: str
    permission_group_id: int
    description: Optional[str]
    created_by_id: Optional[int]
    parser_id: Optional[int]
    permission_group: dict
    external_api_type: Optional[str]
    created_by_username: Optional[str] = None


class IngestCreate(SQLModel):
    name: str
    permission_group_id: int
    description: Optional[str] = None
    parser_id: Optional[int] = None


class IngestUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_group_id: Optional[int] = None
    parser_id: Optional[int] = None


class Ingest(SQLModel, table=True):
    """Main ingest table - the parent of all specific ingest types."""

    __tablename__ = "ingest"

    __table_args__ = (
        Index(
            "ix_ingest_name_permission_group",
            func.lower(Column("name")),
            Column("permission_group_id"),
            unique=True,
        ),
        CheckConstraint(
            "ingest_type IN ('mqtt','sftp','external_api', 'external_sftp')",
            name="ck_ingest_type",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4, unique=True, index=True)
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    created_by_id: Optional[int] = Field(default=None, foreign_key="user.id")
    ingest_type: str = Field(
        description="type used for inheritance", index=True
    )  # e.g., "mqtt", "sftp", "external_api"
    name: str
    permission_group_id: int = Field(foreign_key="permission_group.id")
    description: Optional[str] = None
    parser_id: Optional[int] = Field(foreign_key="parser.id")

    # Relationship to permission user
    user: Optional["User"] = Relationship(back_populates="ingests")

    # Relationship to permission group
    permission_group: "PermissionGroup" = Relationship(back_populates="ingest")

    # Parser
    parser: Optional["Parser"] = Relationship(back_populates="ingest")

    # Relationships to child tables
    mqtt_detail: Optional["IngestMqtt"] = Relationship(
        back_populates="ingest", cascade_delete=True
    )
    sftp_detail: Optional["IngestSftp"] = Relationship(
        back_populates="ingest", cascade_delete=True
    )
    external_sftp_detail: Optional["IngestExternalSftp"] = Relationship(
        back_populates="ingest", cascade_delete=True
    )
    external_api_detail: Optional["IngestExternalApi"] = Relationship(
        back_populates="ingest", cascade_delete=True
    )
