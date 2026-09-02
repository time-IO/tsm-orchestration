from sqlalchemy import Column
from sqlmodel import Field, SQLModel, Relationship
from .permission_group import PermissionGroup
from encryption import EncryptedType
from utils import get_connection_string_secure


class Database(SQLModel, table=True):
    __tablename__ = "database"

    id: int | None = Field(default=None, primary_key=True)
    permission_group_id: int = Field(foreign_key="permission_group.id", unique=True)
    name: str | None
    username: str
    password: str = Field(sa_column=Column("password", EncryptedType, nullable=False))
    read_only_username: str
    read_only_password: str = Field(
        sa_column=Column("read_only_password", EncryptedType, nullable=False)
    )
    url: str
    read_only_url: str

    permission_group: "PermissionGroup" = Relationship(back_populates="database")

    @property
    def mqtt_information(self) -> dict:
        from encryption import encryption_service

        return {
            "username": self.username,
            "password": encryption_service.encrypt(self.password),
            "url": get_connection_string_secure(self),
            "ro_username": self.read_only_username,
            "ro_password": encryption_service.encrypt(self.read_only_password),
            "ro_url": get_connection_string_secure(self, readonly=True),
            "schema": self.username,
        }
