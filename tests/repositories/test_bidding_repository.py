# tests/repositories/test_bidding_repository.py
from datetime import datetime, timezone
from src.repositories.bidding_repository import BiddingRepository
from src.db.models import Bidding
from sqlmodel import Session # For type hinting the fixture
import sys
import os

# Ensure src directory is in path to import models
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, "/app")


def test_create_bidding(db_session: Session):
    bidding_repo = BiddingRepository()
    bidding_data = Bidding(
        name="Test Bidding Create",
        description="A test bidding event for creation",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    
    created_bidding = bidding_repo.create(db_session=db_session, obj_in=bidding_data)
    
    assert created_bidding.id is not None
    assert created_bidding.name == "Test Bidding Create"
    assert created_bidding.description == "A test bidding event for creation"
    
    retrieved_bidding = db_session.get(Bidding, created_bidding.id)
    assert retrieved_bidding is not None
    assert retrieved_bidding.name == "Test Bidding Create"

def test_get_bidding(db_session: Session):
    bidding_repo = BiddingRepository()
    bidding_data = Bidding(
        name="Test Bidding Get",
        description="A test bidding event for get",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    created_bidding = bidding_repo.create(db_session=db_session, obj_in=bidding_data)
    
    retrieved_bidding = bidding_repo.get(db_session=db_session, id=created_bidding.id)
    assert retrieved_bidding is not None
    assert retrieved_bidding.id == created_bidding.id
    assert retrieved_bidding.name == "Test Bidding Get"
    
    non_existent_bidding = bidding_repo.get(db_session=db_session, id=99999) # Assuming 99999 does not exist
    assert non_existent_bidding is None

def test_get_multi_bidding(db_session: Session):
    bidding_repo = BiddingRepository()
    bidding1_data = Bidding(name="Bidding Multi 1", start_date=datetime.now(timezone.utc), end_date=datetime.now(timezone.utc))
    bidding2_data = Bidding(name="Bidding Multi 2", start_date=datetime.now(timezone.utc), end_date=datetime.now(timezone.utc))
    bidding_repo.create(db_session=db_session, obj_in=bidding1_data)
    bidding_repo.create(db_session=db_session, obj_in=bidding2_data)
    
    biddings = bidding_repo.get_multi(db_session=db_session)
    assert len(biddings) >= 2 # Could be more if other tests left data and session is not properly isolated by fixture scope
                               # For function scope fixture, this should be exactly 2 if no other data persists.

    biddings_limit_1 = bidding_repo.get_multi(db_session=db_session, limit=1)
    assert len(biddings_limit_1) == 1
    
    biddings_skip_1_limit_1 = bidding_repo.get_multi(db_session=db_session, skip=1, limit=1)
    assert len(biddings_skip_1_limit_1) == 1
    
    # Check if the skipped item is different from the first item without skip
    if len(biddings) > 1 and len(biddings_skip_1_limit_1) > 0 : # ensure there are items to compare
         assert biddings_limit_1[0].id != biddings_skip_1_limit_1[0].id


def test_update_bidding(db_session: Session):
    bidding_repo = BiddingRepository()
    bidding_data = Bidding(
        name="Test Bidding Update",
        description="Initial description",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    created_bidding = bidding_repo.create(db_session=db_session, obj_in=bidding_data)
    
    update_data = Bidding(name="Updated Bidding Name", description="Updated description")
    
    updated_bidding = bidding_repo.update(db_session=db_session, db_obj=created_bidding, obj_in=update_data)
    
    assert updated_bidding is not None
    assert updated_bidding.id == created_bidding.id
    assert updated_bidding.name == "Updated Bidding Name"
    assert updated_bidding.description == "Updated description"
    
    retrieved_bidding = db_session.get(Bidding, created_bidding.id)
    assert retrieved_bidding is not None
    assert retrieved_bidding.name == "Updated Bidding Name"
    assert retrieved_bidding.description == "Updated description"

def test_remove_bidding(db_session: Session):
    bidding_repo = BiddingRepository()
    bidding_data = Bidding(
        name="Test Bidding Remove",
        description="A test bidding event for remove",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    created_bidding = bidding_repo.create(db_session=db_session, obj_in=bidding_data)
    
    removed_bidding = bidding_repo.remove(db_session=db_session, id=created_bidding.id)
    assert removed_bidding is not None
    assert removed_bidding.id == created_bidding.id
    
    retrieved_bidding_after_remove = bidding_repo.get(db_session=db_session, id=created_bidding.id)
    assert retrieved_bidding_after_remove is None
    
    non_existent_removed_bidding = bidding_repo.remove(db_session=db_session, id=99999) # Assuming 99999 does not exist
    assert non_existent_removed_bidding is None
