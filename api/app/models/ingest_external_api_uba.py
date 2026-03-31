from sqlmodel import Field, SQLModel, Relationship, Index, func, column
import uuid as uuid_pkg
from datetime import datetime, timezone
from .permission_group import PermissionGroup


class IngestExternalApiUbaBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    station_id: str
    description: str | None = None
    sync_enabled: bool = False


class IngestExternalApiUbaCreate(IngestExternalApiUbaBase):
    pass


class IngestExternalApiUbaUpdate(SQLModel):
    permission_group_id: int | None
    name: str | None
    station_id: str | None
    description: str | None
    sync_enabled: bool | None


class IngestExternalApiUbaPublic(IngestExternalApiUbaBase):
    id: int
    uuid: uuid_pkg.UUID
    sync_interval_in_minutes: int
    created_by_id: int
    created_at: datetime
    permission_group: "PermissionGroup"


class IngestExternalApiUba(IngestExternalApiUbaBase, table=True):
    __tablename__ = "ingest_external_api_uba"

    __table_args__ = (
        Index(
            "ix_uba_name_permission_group",
            func.lower(column("name")),
            column("permission_group_id"),
            unique=True,
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    sync_interval_in_minutes: int = 60
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    permission_group: "PermissionGroup" = Relationship(
        back_populates="ingest_external_api_uba"
    )

    @property
    def mqtt_information(self) -> dict:
        return {
            "type": "uba",
            "version_id": 1,
            "enabled": self.sync_enabled,
            "sync_interval": self.sync_interval_in_minutes,
            "settings": {
                "station_id": self.station_id,
            },
        }
