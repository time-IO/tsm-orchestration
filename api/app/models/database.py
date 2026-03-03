from sqlalchemy import Column
from sqlmodel import Field, SQLModel, Relationship
from .permission_group import PermissionGroup
from encryption import EncryptedType


class Database(SQLModel, table=True):
    __tablename__ = "database"

    id: int | None = Field(default=None, primary_key=True)
    permission_group_id: int = Field(foreign_key="permission_group.id", unique=True)
    name: str
    username: str
    password: str = Field(sa_column=Column("password", EncryptedType, nullable=False))
    read_only_username: str
    read_only_password: str = Field(
        sa_column=Column("read_only_password", EncryptedType, nullable=False)
    )
    url: str

    permission_group: "PermissionGroup" = Relationship(back_populates="database")
