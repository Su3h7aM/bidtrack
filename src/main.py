import os
import sys

# This allows running src/main.py directly.
# It adds the project root to sys.path so `from src...` imports work.
# This must be done before any 'from src...' imports.
current_dir_for_main = os.path.dirname(os.path.abspath(__file__))
project_root_for_main = os.path.dirname(current_dir_for_main)
if project_root_for_main not in sys.path:
    sys.path.insert(0, project_root_for_main)

from datetime import datetime, timezone
from sqlmodel import SQLModel, Session # Session for type hint if needed

from src.db.database import engine, get_session
from src.db.models import Bidding, Item
from src.repositories.bidding_repository import BiddingRepository
from src.repositories.item_repository import ItemRepository

def create_db_and_tables():
    print("Creating database and tables if they don't exist...")
    SQLModel.metadata.create_all(engine) # Creates tables if they don't exist
    print("Database and tables should be ready.")

def run_example():
    print("\n--- Running Repository Example ---")
    
    # Correctly use the get_session generator with a context manager
    with next(get_session()) as db:
        bidding_repo = BiddingRepository()
        item_repo = ItemRepository()

        print("\nCreating a new bidding...")
        # Using a unique name to avoid issues if run multiple times without cleaning DB
        bidding_name = f"Summer Tech Expo {datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        new_bidding_data = Bidding(
            name=bidding_name,
            description="Annual technology exhibition and conference.",
            start_date=datetime(2024, 7, 15, 9, 0, 0, tzinfo=timezone.utc),
            end_date=datetime(2024, 7, 17, 17, 0, 0, tzinfo=timezone.utc)
        )
        created_bidding = bidding_repo.create(db_session=db, obj_in=new_bidding_data)
        print(f"Created Bidding: {created_bidding}")

        print("\nCreating a new item for the bidding...")
        item_name = f"Exhibition Booth {datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        new_item_data = Item(
            name=item_name,
            description="Standard 10x10 booth space.",
            bidding_id=created_bidding.id,
            bidding=created_bidding # As per test findings, set the relationship object
        )
        created_item = item_repo.create(db_session=db, obj_in=new_item_data)
        print(f"Created Item: {created_item}")
        if created_item.bidding_id != created_bidding.id:
            print(f"WARNING: Item's bidding_id ({created_item.bidding_id}) does not match Bidding's id ({created_bidding.id})")


        print("\nRetrieving the bidding and its items...")
        # Re-fetch the bidding object to ensure relationship attributes are loaded
        db.refresh(created_bidding) # Refresh to get relationships like 'items'
        retrieved_bidding = bidding_repo.get(db_session=db, id=created_bidding.id)
        
        if retrieved_bidding:
            print(f"Retrieved Bidding: {retrieved_bidding}")
            print(f"Items in Bidding (via relationship): {retrieved_bidding.items}")
            if not retrieved_bidding.items:
                print("Note: 'items' list is empty. This could be due to how the relationship is configured or session state.")
        else:
            print("Failed to retrieve the bidding.")

def main():
    print("Hello from bidtrack!")
    print("Running database example...")
    create_db_and_tables()
    run_example()
    print("\nDatabase example finished.")

if __name__ == "__main__":
    main()
