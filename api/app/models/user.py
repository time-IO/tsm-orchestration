from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)
    username: str
    email: str
    given_name: str
    family_name: str
    active: bool = True
    is_superuser: bool = False