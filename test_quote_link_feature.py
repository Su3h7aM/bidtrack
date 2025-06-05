import sys
import os
from decimal import Decimal

# Adjust PYTHONPATH to include the 'src' directory if the script is in the root
# This allows imports like `from src.db.models import ...`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from sqlmodel import SQLModel, create_engine, Field, Session

# Assuming models are in src.db.models
from src.db.models import Quote, Item, Supplier, Bidding, BiddingMode

# Assuming repository is in src.repository.sqlmodel
from src.repository.sqlmodel import SQLModelRepository

# Assuming service is in src.services.dataframes
from src.services.dataframes import get_quotes_dataframe

def run_quote_link_tests():
    print("Starting Quote link feature test...")

    # 1. Setup
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine) # Create tables in the in-memory database

    # 2. Initialize Repositories
    bidding_repo = SQLModelRepository(Bidding, db_url="sqlite:///:memory:", engine_instance=engine)
    item_repo = SQLModelRepository(Item, db_url="sqlite:///:memory:", engine_instance=engine)
    supplier_repo = SQLModelRepository(Supplier, db_url="sqlite:///:memory:", engine_instance=engine)
    quote_repo = SQLModelRepository(Quote, db_url="sqlite:///:memory:", engine_instance=engine)

    # 3. Create Prerequisite Data
    print("Creating prerequisite data...")
    test_bidding = bidding_repo.add(Bidding(city="Test City", mode=BiddingMode.PE, process_number="BP001"))
    assert test_bidding.id is not None, "Bidding creation failed"

    test_item = item_repo.add(Item(name="Test Item 1", quantity=10, bidding_id=test_bidding.id))
    assert test_item.id is not None, "Item creation failed"

    test_supplier = supplier_repo.add(Supplier(name="Test Supplier Inc."))
    assert test_supplier.id is not None, "Supplier creation failed"
    print("Prerequisite data created.")

    # 4. Test Quote Creation
    print("Testing Quote creation with link...")
    initial_link = "http://example.com/product1"
    new_quote_data = Quote(
        item_id=test_item.id,
        supplier_id=test_supplier.id,
        price=Decimal("100.00"),
        margin=20.0, # Assuming margin is a float percent
        link=initial_link
    )
    created_quote = quote_repo.add(new_quote_data)
    assert created_quote.id is not None, "Quote creation failed"
    assert created_quote.link == initial_link, f"Quote link mismatch after creation. Expected {initial_link}, got {created_quote.link}"
    print(f"Quote created successfully with ID: {created_quote.id} and link: {created_quote.link}")

    # 5. Test Quote Update
    print("Testing Quote update for link...")
    updated_link = "http://example.com/product1-updated"
    # Ensure 'id' is not in the update dict for SQLModelRepository
    update_data = {"link": updated_link, "notes": "Updated notes"}

    # The update method in SQLModelRepository expects item_id and then a dictionary of updates.
    # Let's ensure the repository's update method is compatible or adjust this call.
    # Assuming quote_repo.update(item_id, data_dict)
    updated_quote_model = quote_repo.update(created_quote.id, update_data)
    assert updated_quote_model is not None, "Quote update failed"

    retrieved_after_update = quote_repo.get(created_quote.id)
    assert retrieved_after_update is not None, "Failed to retrieve quote after update"
    assert retrieved_after_update.link == updated_link, f"Quote link mismatch after update. Expected {updated_link}, got {retrieved_after_update.link}"
    print(f"Quote link updated successfully to: {retrieved_after_update.link}")

    # 6. Test get_quotes_dataframe Service
    print("Testing get_quotes_dataframe service...")
    all_quotes = quote_repo.get_all()
    all_items = item_repo.get_all()
    all_suppliers = supplier_repo.get_all()

    quotes_df = get_quotes_dataframe(quotes_list=all_quotes, suppliers_list=all_suppliers, items_list=all_items)

    assert not quotes_df.empty, "DataFrame should not be empty"
    print(f"DataFrame columns: {quotes_df.columns.tolist()}")
    assert 'link' in quotes_df.columns, "'link' column is missing from DataFrame"

    # Find the row for our test quote
    # Assuming 'id' in quotes_df corresponds to quote.id
    test_quote_row = quotes_df[quotes_df['id'] == created_quote.id]
    assert not test_quote_row.empty, "Test quote not found in DataFrame"

    link_from_df = test_quote_row['link'].iloc[0]
    assert link_from_df == updated_link, f"Link in DataFrame mismatch. Expected {updated_link}, got {link_from_df}"
    print("get_quotes_dataframe service test passed for 'link' field.")

    print("All Quote link feature tests passed successfully!")

if __name__ == "__main__":
    run_quote_link_tests()
