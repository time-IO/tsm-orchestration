from sqlmodel import Field, SQLModel
import uuid as uuid_pkg
from datetime import datetime, timezone
from .mqtt_parser import MqttParser

class IngestMqttBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    description: str | None = None
    topic: str
    mqtt_parser_id: int = Field(foreign_key="mqtt_parser.id")

class IngestMqttCreate(IngestMqttBase):
    pass

class IngestMqttUpdate(SQLModel):
    project_id: int | None = None
    name: str | None = None
    description: str | None = None
    topic: str | None = None
    mqtt_parser_id: int | None = None

class IngestMqttPublic(IngestMqttBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime

class IngestMqtt(IngestMqttBase, table=True):
    __tablename__ = "ingest_mqtt"

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    username: str
    password: str
    password_hashed: str
    uri: str