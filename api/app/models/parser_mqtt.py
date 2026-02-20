from sqlmodel import Field, SQLModel, Relationship

from models import IngestMqtt


class MqttParser(SQLModel, table=True):
    __tablename__ = "mqtt_parser"

    id: int | None = Field(default=None, primary_key=True)
    name: str

    ingest_mqtt: list[IngestMqtt] = Relationship(back_populates="mqtt_parser")
