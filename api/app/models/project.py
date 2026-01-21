from sqlmodel import Field, SQLModel, Relationship
import uuid as uuid_pkg

class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    
    ingest_external_api_uba: list["IngestExternalApiUba"] = Relationship(back_populates="project")

# fix to avoid circular imports    
from .ingest_external_api_uba import IngestExternalApiUba
Project.model_rebuild()