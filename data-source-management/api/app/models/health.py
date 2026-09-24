from sqlmodel import SQLModel


class Health(SQLModel):
    status: str
