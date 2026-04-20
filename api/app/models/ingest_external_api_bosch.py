from sqlmodel import Field, SQLModel, Relationship, Column, Index, func, column
import uuid as uuid_pkg
from datetime import datetime, timezone
from .permission_group import PermissionGroup
from encryption import EncryptedType


class IngestExternalApiBoschBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    description: str | None = None
    sync_enabled: bool = False
    sync_interval_in_minutes: int | None = Field(nullable=True)
    endpoint: str
    sensor_id: str
    bosch_username: str
    bosch_password: str
    period_in_minutes: int


class IngestExternalApiBoschCreate(IngestExternalApiBoschBase):
    pass


class IngestExternalApiBoschUpdate(SQLModel):
    permission_group_id: int | None = None
    name: str | None = None
    description: str | None = None
    sync_interval_in_minutes: int | None = None
    sync_enabled: bool | None = None
    endpoint: str | None = None
    sensor_id: str | None = None
    username: str | None = None
    password: str | None = None
    period_in_minutes: int | None = None


class IngestExternalApiBoschPublic(IngestExternalApiBoschBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int | None = None
    created_at: datetime
    permission_group: "PermissionGroup"


class IngestExternalApiBosch(IngestExternalApiBoschBase, table=True):
    __tablename__ = "ingest_external_api_bosch"

    __table_args__ = (
        Index(
            "ix_bosch_name_permission_group",
            func.lower(column("name")),
            column("permission_group_id"),
            unique=True,
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int | None = Field(foreign_key="user.id", nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    bosch_password: str = Field(
        sa_column=Column("bosch_password", EncryptedType, nullable=False)
    )

    permission_group: "PermissionGroup" = Relationship(
        back_populates="ingest_external_api_bosch"
    )

    @property
    def mqtt_information(self) -> dict:
        from encryption import encryption_service

        return {
            "type": "bosch",
            "version_id": 1,
            "enabled": self.sync_enabled,
            "sync_interval": self.sync_interval_in_minutes,
            "settings": {
                "period": self.period_in_minutes,
                "endpoint": self.endpoint,
                "username": self.bosch_username,
                "password": encryption_service.encrypt(self.bosch_password),
                "sensor_id": self.sensor_id,
            },
        }
