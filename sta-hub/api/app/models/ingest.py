from uuid import UUID

from pydantic import BaseModel


class Ingest(BaseModel):
    id: int
    uuid: UUID
    name: str
    permission_group_id: int
    permission_group_name: str | None = None


class IngestsResponse(BaseModel):
    items: list[Ingest]
