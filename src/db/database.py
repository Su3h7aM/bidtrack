from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///data/bidtrack.db"

engine = create_engine(DATABASE_URL)


def init_db():
    SQLModel.metadata.create_all(engine)


def db_add(table):
    with Session(engine) as session:
        session.add(table)
        session.commit()
        session.refresh(table)

    return table
