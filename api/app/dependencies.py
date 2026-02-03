from sqlmodel import Session, create_engine
from .config import settings

engine = create_engine(str(settings.DATABASE_URI))

def get_session():
    with Session(engine) as session:
        yield session