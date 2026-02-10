from sqlmodel import Field, SQLModel
from datetime import datetime, timezone


class UserPublic(SQLModel):
    id: int
    username: str
    email: str
    given_name: str
    family_name: str
    is_active: bool
    is_superuser: bool


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)
    sub: str = Field(
        index=True,
        unique=True,
        nullable=False,
        description="OIDC subject identifier",
    )
    username: str
    email: str
    given_name: str
    family_name: str
    is_active: bool = True
    is_superuser: bool = False

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
