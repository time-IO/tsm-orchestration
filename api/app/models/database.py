from sqlmodel import Field, SQLModel

class Database(SQLModel, table=True):
    __tablename__ = "database"

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    schema: str
    username: str
    password: str
    ro_user: str
    ro_password: str