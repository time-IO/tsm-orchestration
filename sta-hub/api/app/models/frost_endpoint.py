from pydantic import BaseModel


class FrostEndpoint(BaseModel):
    name: str
    display_name: str
    group: str
    project: str | None = None
    url: str
    public_url: str = ""
    internal_url: str = ""
    is_internal: bool = False


class FrostEndpointsResponse(BaseModel):
    endpoints: list[FrostEndpoint]
