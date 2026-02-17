from sqlmodel import Field, SQLModel


class NeutronMonitorStation(SQLModel, table=True):
    __tablename__ = "neutron_monitor_station"

    id: int | None = Field(default=None, primary_key=True)
    station_id: str
    description: str
