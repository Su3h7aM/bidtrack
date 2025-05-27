from sqlmodel import create_engine, Session

# Define the database URL.
# For consistency, use the same SQLite URL as in alembic.ini.
# In a real application, this would come from environment variables or a config file.
DATABASE_URL = "sqlite:///./bidtrack.db"

# Create the SQLModel engine.
# echo=True is good for development as it logs SQL statements.
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    """
    Provides a database session.
    This is typically used with a try...finally block or as a dependency
    in frameworks like FastAPI.
    """
    with Session(engine) as session:
        yield session
