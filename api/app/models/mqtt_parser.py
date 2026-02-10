from sqlmodel import Field, SQLModel


class MqttParser(SQLModel, table=True):
    __tablename__ = "mqtt_parser"

    id: int | None = Field(default=None, primary_key=True)
    name: str
