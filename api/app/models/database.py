from sqlmodel import Field, SQLModel, Relationship

from models import PermissionGroup


class Database(SQLModel, table=True):
    __tablename__ = "database"

    id: int | None = Field(default=None, primary_key=True)
    permission_group_id: int = Field(foreign_key="permission_group.id")
    schema_name: str
    username: str
    password: str
    ro_user: str
    ro_password: str

    permission_group: PermissionGroup = Relationship(back_populates="database")
