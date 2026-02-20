from sqlmodel import Field, SQLModel, Relationship

from models import IngestExternalApiNeutronMonitor


class NeutronMonitorStation(SQLModel, table=True):
    __tablename__ = "neutron_monitor_station"

    id: int | None = Field(default=None, primary_key=True)
    station_id: str
    description: str

    ingest_external_api_neutron_monitor: IngestExternalApiNeutronMonitor = Relationship(
        back_populates="station"
    )
