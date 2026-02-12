from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone

from .permission_group import PermissionGroup, PermissionGroupUserLink


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

    permission_groups: list["PermissionGroup"] = Relationship(
        back_populates="users", link_model=PermissionGroupUserLink
    )

    @property
    def permission_group_ids(self) -> list[int]:
        return [pg.id for pg in self.permission_groups]
