from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
import uuid as uuid_pkg
from datetime import datetime, timezone

from models import PermissionGroup, MqttParser


class IngestMqttBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    description: str | None = None
    topic: str
    uri: str
    mqtt_parser_id: int = Field(foreign_key="mqtt_parser.id")


class IngestMqttCreate(IngestMqttBase):
    pass


class IngestMqttUpdate(SQLModel):
    permission_group_id: int | None = None
    name: str | None = None
    description: str | None = None
    topic: str | None = None
    uri: str | None = None
    mqtt_parser_id: int | None = None


class IngestMqttPublic(IngestMqttBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime
    permission_group: PermissionGroup
    username: str
    password: str
    mqtt_parser: MqttParser


class IngestMqtt(IngestMqttBase, table=True):
    __tablename__ = "ingest_mqtt"

    __table_args__ = (
        UniqueConstraint(
            "name", "permission_group_id", name="mqtt_unique_name_permission_group"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    username: str
    password: str
    password_hashed: str

    permission_group: PermissionGroup = Relationship(back_populates="ingest_mqtt")
    mqtt_parser: MqttParser = Relationship(back_populates="ingest_mqtt")

    # Override model_post_init to ensure username is set correctly
    def model_post_init(self, __context) -> None:
        print("POST INIT")
        if not self.username:
            self.username = f"ingest-mqtt-{self.uuid}"
