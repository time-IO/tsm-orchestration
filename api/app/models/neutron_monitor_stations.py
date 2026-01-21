from sqlmodel import Field, SQLModel

class NeutronMonitorStations(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    station_id: str
    description: str