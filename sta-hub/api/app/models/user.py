from pydantic import BaseModel


class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    given_name: str
    family_name: str
    is_active: bool
    is_superuser: bool
