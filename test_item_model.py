import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime # Required for Bidding.date if not defaulted

# Attempt to import models, adjust path if necessary based on project structure
# Assuming 'src' is in PYTHONPATH or tests are run from project root
from src.db.models import Item, Bidding, BiddingMode

# Setup for an in-memory SQLite database for testing
# Using a unique name for the in-memory DB for clarity, though :memory: is fine
engine = create_engine("sqlite:///./test_item_model.db") # Using a file for inspection if needed, :memory: for pure in-memory

@pytest.fixture(scope="function", autouse=True)
def create_db_and_tables_fixture():
    """Creates all tables before each test and drops them after."""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def session_fixture() -> Session: # Added return type hint
    """Provides a database session for each test."""
    with Session(engine) as session:
        yield session

@pytest.fixture
def dummy_bidding_fixture(session_fixture: Session) -> Bidding: # Added return type hint
    """Creates a prerequisite Bidding record for tests."""
    # Bidding model requires city, mode, process_number. Date can be default.
    bidding = Bidding(
        city="Test City",
        mode=BiddingMode.PE, # Using Enum member
        process_number="123/2024",
        date=datetime.now() # Explicitly setting date
    )
    session_fixture.add(bidding)
    session_fixture.commit()
    session_fixture.refresh(bidding)
    return bidding

def test_item_name_cannot_be_null(session_fixture: Session, dummy_bidding_fixture: Bidding):
    """Tests that an Item cannot be created with a null name."""
    with pytest.raises(IntegrityError):
        item_with_null_name = Item(
            name=None,  # This should cause the IntegrityError
            code="ITM000",
            unit="UN",
            quantity=10.0, # Ensure float
            bidding_id=dummy_bidding_fixture.id
        )
        session_fixture.add(item_with_null_name)
        session_fixture.commit()

def test_item_name_can_be_duplicate(session_fixture: Session, dummy_bidding_fixture: Bidding):
    """Tests that multiple Items can have the same name."""
    item1_name = "Duplicate Test Name"

    # Item requires: code, name, unit, quantity, bidding_id
    item1 = Item(
        name=item1_name,
        code="ITM001",
        unit="UN",
        quantity=10.0, # Ensure float
        bidding_id=dummy_bidding_fixture.id
    )
    item2 = Item(
        name=item1_name,  # Same name as item1
        code="ITM002",    # Different code
        unit="EA",
        quantity=5.0,   # Ensure float
        bidding_id=dummy_bidding_fixture.id
    )

    session_fixture.add(item1)
    session_fixture.add(item2)
    session_fixture.commit()

    retrieved_item1 = session_fixture.get(Item, item1.id)
    retrieved_item2 = session_fixture.get(Item, item2.id)

    assert retrieved_item1 is not None, "Item1 should be retrievable"
    assert retrieved_item1.name == item1_name, "Item1 name mismatch"
    assert retrieved_item2 is not None, "Item2 should be retrievable"
    assert retrieved_item2.name == item1_name, "Item2 name mismatch"
    assert retrieved_item1.id != retrieved_item2.id, "Items should have different IDs"
    assert retrieved_item1.code != retrieved_item2.code, "Items should have different codes"
