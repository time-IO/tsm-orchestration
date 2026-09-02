from sqlmodel import SQLModel, Field, CheckConstraint, Relationship
from typing import Optional
from .ingest import Ingest, IngestRead, IngestCreate, IngestUpdate


class IngestExternalApiRead(IngestRead):
    api_type: str
    sync_enabled: bool
    sync_interval_in_minutes: Optional[int] = None


class IngestExternalApiCreate(IngestCreate):
    sync_enabled: bool = False
    sync_interval_in_minutes: Optional[int] = None


class IngestExternalApiUpdate(IngestUpdate):
    sync_enabled: Optional[bool] = None
    sync_interval_in_minutes: Optional[int] = None


class IngestExternalApi(SQLModel, table=True):
    __tablename__ = "ingest_external_api"

    __table_args__ = (
        CheckConstraint(
            "api_type IN ('bosch','dwd','nm', 'ttn','tsystems','uba', 'sensoto')",
            name="ck_api_type",
        ),
    )

    ingest_id: int = Field(
        foreign_key="ingest.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    api_type: str = Field(
        description="type used for inheritance", index=True
    )  # e.g., "bosch", "dwd", etc.
    sync_enabled: bool = False
    sync_interval_in_minutes: Optional[int]

    # Relationship to specific API implementations
    ## parent
    ingest: Ingest = Relationship(back_populates="external_api_detail")
    ## children
    bosch_detail: Optional["IngestExternalApiBosch"] = Relationship(
        back_populates="external_api", cascade_delete=True
    )
    dwd_detail: Optional["IngestExternalApiDwd"] = Relationship(
        back_populates="external_api", cascade_delete=True
    )
    neutron_monitor_detail: Optional["IngestExternalApiNeutronMonitor"] = Relationship(
        back_populates="external_api", cascade_delete=True
    )
    sensoto: Optional["IngestExternalApiSensoto"] = Relationship(
        back_populates="external_api", cascade_delete=True
    )
    the_things_network_detail: Optional["IngestExternalApiTheThingsNetwork"] = (
        Relationship(back_populates="external_api", cascade_delete=True)
    )
    tsystems_detail: Optional["IngestExternalApiTSystems"] = Relationship(
        back_populates="external_api", cascade_delete=True
    )
    uba_detail: Optional["IngestExternalApiUba"] = Relationship(
        back_populates="external_api", cascade_delete=True
    )
