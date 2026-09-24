from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from access_scope import AccessScope

if TYPE_CHECKING:
    from .ingest import Ingest
    from .parser_detailed import ParserDetailed
    from .quality_control_setting import QualityControlSetting

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

    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    permission_groups: list["PermissionGroup"] = Relationship(
        back_populates="users", link_model=PermissionGroupUserLink
    )

    ingests: list["Ingest"] = Relationship(back_populates="user")

    parser_detailed: list["ParserDetailed"] = Relationship(back_populates="user")

    quality_control_setting: list["QualityControlSetting"] = Relationship(
        back_populates="user"
    )

    @property
    def permission_group_ids(self) -> list[int]:
        return [pg.id for pg in self.permission_groups]

    @property
    def access_scope(self) -> AccessScope:
        return AccessScope.from_user(self)
