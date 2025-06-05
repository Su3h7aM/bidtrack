from sqlmodel import SQLModel, Session, create_engine
import os
from collections.abc import Generator

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is not None:
    engine = create_engine(DATABASE_URL)


def init_db():
    # SQLModel.metadata.create_all(engine)
    pass


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
