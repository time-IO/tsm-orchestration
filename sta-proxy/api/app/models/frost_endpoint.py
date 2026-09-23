from pydantic import BaseModel


class FrostEndpoint(BaseModel):
    name: str
    displayName: str
    group: str
    project: str | None = None
    url: str


class FrostEndpointsResponse(BaseModel):
    endpoints: list[FrostEndpoint]
