from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional
from encryption import EncryptedType
from .ingest import Ingest, IngestRead, IngestCreate, IngestUpdate


class IngestExternalMqttRead(IngestRead):
    external_mqtt_address: str
    external_mqtt_port: int
    external_mqtt_username: str
    external_mqtt_password: str
    external_mqtt_ca_cert: str
    external_mqtt_client_cert: str
    external_mqtt_client_key: str
    external_mqtt_topic: str
    enabled: bool


class IngestExternalMqttCreate(IngestCreate):
    external_mqtt_address: str
    external_mqtt_port: int
    external_mqtt_username: Optional[str] = None
    external_mqtt_password: Optional[str] = None
    external_mqtt_ca_cert: Optional[str] = None
    external_mqtt_client_cert: Optional[str] = None
    external_mqtt_client_key: Optional[str] = None
    external_mqtt_topic: str
    enabled: bool = False


class IngestExternalMqttUpdate(IngestUpdate):
    external_mqtt_address: Optional[str] = None
    external_mqtt_port: Optional[int] = None
    external_mqtt_username: Optional[str] = None
    external_mqtt_password: Optional[str] = None
    external_mqtt_ca_cert: Optional[str] = None
    external_mqtt_client_cert: Optional[str] = None
    external_mqtt_client_key: Optional[str] = None
    external_mqtt_topic: Optional[str] = None
    enabled: Optional[bool] = None


class IngestExternalMqtt(SQLModel, table=True):
    __tablename__ = "ingest_external_mqtt"

    ingest_id: int = Field(
        foreign_key="ingest.id", primary_key=True, ondelete="CASCADE"
    )

    external_mqtt_address: str
    external_mqtt_port: int
    external_mqtt_username: str
    external_mqtt_password: str = Field(
        sa_column=Column("external_mqtt_password", EncryptedType, nullable=True)
    )
    external_mqtt_ca_cert: str = Field(
        sa_column=Column("external_mqtt_ca_cert", EncryptedType, nullable=True)
    )
    external_mqtt_client_cert: str = Field(
        sa_column=Column("external_mqtt_client_cert", EncryptedType, nullable=True)
    )
    external_mqtt_client_key: str = Field(
        sa_column=Column("external_mqtt_client_key", EncryptedType, nullable=True)
    )
    external_mqtt_topic: str
    enabled: bool = False

    ingest: Ingest = Relationship(back_populates="external_mqtt_detail")

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
