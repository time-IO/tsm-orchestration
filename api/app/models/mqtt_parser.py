from sqlmodel import Field, SQLModel, Relationship


class MqttParser(SQLModel, table=True):
    __tablename__ = "mqtt_parser"

    id: int | None = Field(default=None, primary_key=True)
    name: str

    ingest_mqtt: list["IngestMqtt"] = Relationship(back_populates="mqtt_parser")


from .ingest_mqtt import IngestMqtt
