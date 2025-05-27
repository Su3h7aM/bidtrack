# tests/conftest.py
import pytest
from sqlmodel import create_engine, Session, SQLModel
from typing import Generator
import sys
import os

# Ensure src directory is in path to import models
# This assumes conftest.py is in the 'tests' directory at the project root.
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, "/app")


# Import your models to ensure they are registered with SQLModel.metadata
from src.db.models import Bidding, Item # Adjust if your models are elsewhere

TEST_DATABASE_URL = "sqlite:///:memory:" # In-memory SQLite

@pytest.fixture(scope="function", name="engine")
def fixture_engine():
    engine = create_engine(TEST_DATABASE_URL, echo=False) # Echo can be noisy for tests
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function", name="db_session")
def fixture_db_session(engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
