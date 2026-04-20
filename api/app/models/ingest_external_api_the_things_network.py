from sqlmodel import Field, SQLModel, Relationship, Column, Index, func, column
import uuid as uuid_pkg
from datetime import datetime, timezone
from .permission_group import PermissionGroup
from encryption import EncryptedType


class IngestExternalApiTheThingsNetworkBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    description: str | None = None
    sync_interval_in_minutes: int | None = Field(nullable=True)
    sync_enabled: bool = False
    api_key: str
    endpoint_uri: str


class IngestExternalApiTheThingsNetworkCreate(IngestExternalApiTheThingsNetworkBase):
    pass


class IngestExternalApiTheThingsNetworkUpdate(SQLModel):
    permission_group_id: int | None = None
    name: str | None = None
    description: str | None = None
    sync_interval_in_minutes: int | None = None
    sync_enabled: bool | None = None
    api_key: str | None = None
    endpoint_uri: str | None = None


class IngestExternalApiTheThingsNetworkPublic(IngestExternalApiTheThingsNetworkBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int | None = None
    created_at: datetime
    permission_group: "PermissionGroup"


class IngestExternalApiTheThingsNetwork(
    IngestExternalApiTheThingsNetworkBase, table=True
):
    __tablename__ = "ingest_external_api_the_things_network"

    __table_args__ = (
        Index(
            "ix_ttn_name_permission_group",
            func.lower(column("name")),
            column("permission_group_id"),
            unique=True,
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int | None = Field(foreign_key="user.id", nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    api_key: str = Field(sa_column=Column("api_key", EncryptedType, nullable=False))

    permission_group: "PermissionGroup" = Relationship(
        back_populates="ingest_external_api_the_things_network"
    )

    @property
    def mqtt_information(self) -> dict:
        from encryption import encryption_service

        return {
            "type": "ttn",
            "version_id": 1,
            "enabled": self.sync_enabled,
            "sync_interval": self.sync_interval_in_minutes,
            "settings": {
                "api_key": encryption_service.encrypt(self.api_key),
                "endpoint_uri": self.endpoint_uri,
            },
        }
