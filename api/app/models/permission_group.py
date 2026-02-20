from sqlmodel import Field, SQLModel, Relationship
import uuid as uuid_pkg
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from .user import User


class PermissionGroupUserLink(SQLModel, table=True):
    __tablename__ = "permission_group_user_link"

    permission_group_id: int | None = Field(
        default=None, primary_key=True, foreign_key="permission_group.id"
    )
    user_id: int | None = Field(default=None, primary_key=True, foreign_key="user.id")


class PermissionGroup(SQLModel, table=True):
    __tablename__ = "permission_group"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    entitlement: str = Field(unique=True)

    users: list["User"] = Relationship(
        back_populates="permission_groups", link_model=PermissionGroupUserLink
    )

    csv_parser: list["CsvParser"] = Relationship(back_populates="permission_group")
    database: list["Database"] = Relationship(back_populates="permission_group")
    ingest_external_api_bosch: list["IngestExternalApiBosch"] = Relationship(
        back_populates="permission_group"
    )
    ingest_external_api_dwd: list["IngestExternalApiDwd"] = Relationship(
        back_populates="permission_group"
    )
    ingest_external_api_neutron_monitor: list["IngestExternalApiNeutronMonitor"] = (
        Relationship(back_populates="permission_group")
    )
    ingest_external_api_the_things_network: list[
        "IngestExternalApiTheThingsNetwork"
    ] = Relationship(back_populates="permission_group")
    ingest_external_api_tsystems: list["IngestExternalApiTSystems"] = Relationship(
        back_populates="permission_group"
    )
    ingest_external_api_uba: list["IngestExternalApiUba"] = Relationship(
        back_populates="permission_group"
    )
    ingest_external_sftp: list["IngestExternalSftp"] = Relationship(
        back_populates="permission_group"
    )
    ingest_mqtt: list["IngestMqtt"] = Relationship(back_populates="permission_group")
    ingest_s3store: list["IngestS3Store"] = Relationship(
        back_populates="permission_group"
    )
    quality_control_setting: list["QualityControlSetting"] = Relationship(
        back_populates="permission_group"
    )

    @staticmethod
    def convert_entitlement_to_name(entitlement):
        """Extract the name from the entitlement."""
        pattern = r"^(.+?):(res|group):(?P<name_part>.+)#(.*)$"
        match_result = re.search(pattern, entitlement)
        if match_result:
            return match_result.group("name_part")
        return entitlement

    @staticmethod
    def get_entitlement_vo(entitlement):
        if ":group:" in entitlement:
            prefix, rest_content = entitlement.split(":group:", 1)
            if ":" in rest_content:
                vo, rest = rest_content.split(":", 1)
                return vo
        return ""


# fix to avoid circular imports
from .parser_csv import CsvParser
from .database import Database
from .ingest_external_api_bosch import IngestExternalApiBosch
from .ingest_external_api_dwd import IngestExternalApiDwd
from .ingest_external_api_neutron_monitor import IngestExternalApiNeutronMonitor
from .ingest_external_api_the_things_network import IngestExternalApiTheThingsNetwork
from .ingest_external_api_tsystems import IngestExternalApiTSystems
from .ingest_external_api_uba import IngestExternalApiUba
from .ingest_external_sftp import IngestExternalSftp
from .ingest_mqtt import IngestMqtt
from .ingest_s3store import IngestS3Store
from .quality_control_setting import QualityControlSetting

PermissionGroup.model_rebuild()
