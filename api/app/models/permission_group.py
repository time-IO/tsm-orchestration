from sqlmodel import Field, SQLModel, Relationship
import uuid as uuid_pkg


class PermissionGroup(SQLModel, table=True):
    __tablename__ = "permission_group"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)

    ingest_external_api_uba: list["IngestExternalApiUba"] = Relationship(
        back_populates="permission_group"
    )


# fix to avoid circular imports
from .ingest_external_api_uba import IngestExternalApiUba

PermissionGroup.model_rebuild()
