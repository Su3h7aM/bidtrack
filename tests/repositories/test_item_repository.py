# tests/repositories/test_item_repository.py
from datetime import datetime, timezone
from src.repositories.item_repository import ItemRepository
from src.repositories.bidding_repository import BiddingRepository # To create a Bidding first
from src.db.models import Item, Bidding
from sqlmodel import Session # For type hinting the fixture
import sys
import os

# Ensure src directory is in path to import models
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, "/app")


def test_create_item(db_session: Session):
    bidding_repo = BiddingRepository()
    item_repo = ItemRepository()
    
    bidding_data = Bidding(name="Bidding for Item Test", start_date=datetime.now(timezone.utc), end_date=datetime.now(timezone.utc))
    created_bidding = bidding_repo.create(db_session=db_session, obj_in=bidding_data)
    
    item_data = Item(
        name="Test Item Create",
        description="A test item for creation",
        bidding_id=created_bidding.id,
        bidding=created_bidding # Explicitly set the relationship object
    )
    created_item = item_repo.create(db_session=db_session, obj_in=item_data)
    
    assert created_item.id is not None
    assert created_item.name == "Test Item Create"
    assert created_item.description == "A test item for creation"
    assert created_item.bidding_id == created_bidding.id
    
    retrieved_item = db_session.get(Item, created_item.id)
    assert retrieved_item is not None
    assert retrieved_item.name == "Test Item Create"
    assert retrieved_item.bidding.name == "Bidding for Item Test" # Check relationship

def test_get_item(db_session: Session):
    bidding_repo = BiddingRepository()
    item_repo = ItemRepository()

    bidding_data = Bidding(name="Bidding for Get Item", start_date=datetime.now(timezone.utc), end_date=datetime.now(timezone.utc))
    created_bidding = bidding_repo.create(db_session=db_session, obj_in=bidding_data)
    
    item_data = Item(name="Test Item Get", bidding_id=created_bidding.id, bidding=created_bidding)
    created_item = item_repo.create(db_session=db_session, obj_in=item_data)
    
    retrieved_item = item_repo.get(db_session=db_session, id=created_item.id)
    assert retrieved_item is not None
    assert retrieved_item.id == created_item.id
    assert retrieved_item.name == "Test Item Get"

    non_existent_item = item_repo.get(db_session=db_session, id=99999)
    assert non_existent_item is None

def test_get_multi_item(db_session: Session):
    bidding_repo = BiddingRepository()
    item_repo = ItemRepository()

    bidding_data = Bidding(name="Bidding for Multi Item", start_date=datetime.now(timezone.utc), end_date=datetime.now(timezone.utc))
    created_bidding = bidding_repo.create(db_session=db_session, obj_in=bidding_data)
    
    item1_data = Item(name="Item Multi 1", bidding_id=created_bidding.id, bidding=created_bidding)
    item2_data = Item(name="Item Multi 2", bidding_id=created_bidding.id, bidding=created_bidding)
    item_repo.create(db_session=db_session, obj_in=item1_data)
    item_repo.create(db_session=db_session, obj_in=item2_data)
    
    items = item_repo.get_multi(db_session=db_session)
    # Filter for items only belonging to this test's bidding, as get_multi is not filtered by bidding_id by default
    items_for_this_bidding = [item for item in items if item.bidding_id == created_bidding.id]
    assert len(items_for_this_bidding) == 2

    items_limit_1 = item_repo.get_multi(db_session=db_session, limit=1)
    # This might pick up items from other tests if not filtered, or if DB is not fully clean.
    # A more robust test would filter by bidding_id or ensure a clean DB per test.
    assert len(items_limit_1) == 1


def test_update_item(db_session: Session):
    bidding_repo = BiddingRepository()
    item_repo = ItemRepository()

    bidding_data = Bidding(name="Bidding for Update Item", start_date=datetime.now(timezone.utc), end_date=datetime.now(timezone.utc))
    created_bidding = bidding_repo.create(db_session=db_session, obj_in=bidding_data)
    
    item_data = Item(name="Test Item Update", description="Initial item description", bidding_id=created_bidding.id, bidding=created_bidding)
    created_item = item_repo.create(db_session=db_session, obj_in=item_data)
    
    update_data = Item(name="Updated Item Name", description="Updated item description") # Only include fields to update
    
    updated_item = item_repo.update(db_session=db_session, db_obj=created_item, obj_in=update_data)
    
    assert updated_item is not None
    assert updated_item.id == created_item.id
    assert updated_item.name == "Updated Item Name"
    assert updated_item.description == "Updated item description"
    
    retrieved_item = db_session.get(Item, created_item.id)
    assert retrieved_item is not None
    assert retrieved_item.name == "Updated Item Name"
    assert retrieved_item.description == "Updated item description"

def test_remove_item(db_session: Session):
    bidding_repo = BiddingRepository()
    item_repo = ItemRepository()

    bidding_data = Bidding(name="Bidding for Remove Item", start_date=datetime.now(timezone.utc), end_date=datetime.now(timezone.utc))
    created_bidding = bidding_repo.create(db_session=db_session, obj_in=bidding_data)

    item_data = Item(name="Test Item Remove", bidding_id=created_bidding.id, bidding=created_bidding)
    created_item = item_repo.create(db_session=db_session, obj_in=item_data)
    
    removed_item = item_repo.remove(db_session=db_session, id=created_item.id)
    assert removed_item is not None
    assert removed_item.id == created_item.id
    
    retrieved_item_after_remove = item_repo.get(db_session=db_session, id=created_item.id)
    assert retrieved_item_after_remove is None
    
    non_existent_removed_item = item_repo.remove(db_session=db_session, id=99999) # Assuming 99999 does not exist
    assert non_existent_removed_item is None
