import os
import sys
from sqlmodel import create_engine, Session
import sqlalchemy as sa # Ensure sqlalchemy is imported for sa.text()
from src.db.models import Bidding, Item, Quote, Bid, BiddingMode, SQLModel, Supplier, Bidder
from src.repository.sqlmodel import SQLModelRepository
from decimal import Decimal
from datetime import datetime, timezone

# Add src to Python path to allow direct imports of src.db.models etc.
# Assumes script is in repo root, and 'src' is a subdir.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))


def run_cascade_delete_test():
    print("Starting cascade delete test with clean DB and FK checks...")

    # Clean Slate: Ensure 'data' directory exists and remove old DB file
    db_file_path = "data/bidtrack.db"
    # Create 'data' directory if it doesn't exist
    os.makedirs(os.path.dirname(db_file_path), exist_ok=True)
    if os.path.exists(db_file_path):
        os.remove(db_file_path)
        print(f"Removed existing database file: {db_file_path}")

    # Database setup
    db_url = f"sqlite:///{db_file_path}"
    engine = create_engine(db_url) # Engine does not implicitly enable foreign_keys for all connections immediately

    print("\nStep -1: Verifying and Enabling PRAGMA foreign_keys=ON...")
    # For SQLite, PRAGMA foreign_keys must be enabled on each connection.
    # SQLAlchemy handles this by default for SQLite dialect by issuing the PRAGMA on connect.
    # This check confirms that behavior for a new connection.
    with engine.connect() as connection:
        connection.execute(sa.text("PRAGMA foreign_keys = ON;")) # Ensure it's on for this connection
        fk_status_result = connection.execute(sa.text("PRAGMA foreign_keys;")).fetchone()
        if fk_status_result and fk_status_result[0] == 1:
            print("  SUCCESS: PRAGMA foreign_keys is ON for this connection.")
        else:
            # This should ideally not happen with modern SQLAlchemy & SQLite
            print("  ERROR: Failed to enable/confirm PRAGMA foreign_keys for this connection. Cascades might not work as expected by the DB.")
            # Raise an error because the test integrity depends on this
            raise RuntimeError("Failed to enable PRAGMA foreign_keys for the SQLite connection.")

    # Create tables AFTER ensuring engine/connections will respect foreign keys.
    SQLModel.metadata.create_all(engine)

    print("\nStep 0: Inspecting 'item' table foreign key for 'bidding_id' ON DELETE CASCADE...")
    with engine.connect() as connection:
        # Need to ensure FKs are on for this inspection connection too.
        connection.execute(sa.text("PRAGMA foreign_keys = ON;"))
        result = connection.execute(sa.text("PRAGMA foreign_key_list('item');"))
        fk_info_found = False
        for row_tuple in result:
            # id, seq, table, from, to, on_update, on_delete, match
            fk_from_col = row_tuple[3] # 'from' column name
            fk_on_delete_action = row_tuple[6] # 'on_delete' action

            print(f"Raw FK info: id={row_tuple[0]}, seq={row_tuple[1]}, referenced_table={row_tuple[2]}, from_column={fk_from_col}, to_column={row_tuple[4]}, on_update={row_tuple[5]}, on_delete={fk_on_delete_action}, match={row_tuple[7]}")

            if fk_from_col == 'bidding_id':
                fk_info_found = True
                print(f"Foreign key details for 'item.bidding_id': ON DELETE is '{fk_on_delete_action}'")
                if fk_on_delete_action == 'CASCADE':
                    print("  SUCCESS: ON DELETE CASCADE is correctly set for item.bidding_id.")
                else:
                    print(f"  ERROR: ON DELETE for item.bidding_id is '{fk_on_delete_action}', NOT 'CASCADE'.")
                    raise RuntimeError(f"Schema check failed: item.bidding_id ON DELETE is not CASCADE (is {fk_on_delete_action})")
                break
        if not fk_info_found:
            print("ERROR: Could not find foreign key information for 'bidding_id' in 'item' table via PRAGMA.")
            raise RuntimeError("Schema check failed: No FK found for item.bidding_id")

    # Repositories (will use new connections from the engine)
    bidding_repo = SQLModelRepository(model=Bidding, engine_instance=engine)
    item_repo = SQLModelRepository(model=Item, engine_instance=engine)
    quote_repo = SQLModelRepository(model=Quote, engine_instance=engine)
    bid_repo = SQLModelRepository(model=Bid, engine_instance=engine)
    supplier_repo = SQLModelRepository(model=Supplier, engine_instance=engine)
    bidder_repo = SQLModelRepository(model=Bidder, engine_instance=engine)

    def get_or_create_supplier(name="TestCascadeSupplier"):
        # Repos uses its own session, which should benefit from SQLAlchemy's on_connect for FKs
        with Session(engine) as session: # Create a new session for this operation
            supplier = session.query(Supplier).filter(Supplier.name == name).first()
            if supplier:
                # print(f"Using existing Supplier: {supplier.name} (ID: {supplier.id})") # Reduced verbosity
                return supplier
            supplier = Supplier(name=name, email=f"{name.lower()}@example.com", website=f"http://{name.lower()}.example.com", phone="1234567890")
            session.add(supplier)
            session.commit()
            session.refresh(supplier)
            print(f"Created Supplier: {supplier.name} (ID: {supplier.id})")
            return supplier

    def get_or_create_bidder(name="TestCascadeBidder"):
        with Session(engine) as session:
            bidder = session.query(Bidder).filter(Bidder.name == name).first()
            if bidder:
                # print(f"Using existing Bidder: {bidder.name} (ID: {bidder.id})") # Reduced verbosity
                return bidder
            bidder = Bidder(name=name, email=f"{name.lower()}@example.com", website=f"http://{name.lower()}.example.com", phone="0987654321")
            session.add(bidder)
            session.commit()
            session.refresh(bidder)
            print(f"Created Bidder: {bidder.name} (ID: {bidder.id})")
            return bidder

    print("\nStep 1: Creating dependent entities (Supplier/Bidder)...")
    test_supplier = get_or_create_supplier()
    test_bidder = get_or_create_bidder()
    print(f"Test Supplier ID: {test_supplier.id}, Test Bidder ID: {test_bidder.id}")

    print("\nStep 2: Creating main test data (Bidding, Items, Quotes, Bids)...")
    # Using timestamp for unique process_number to avoid collisions on reruns if DB wasn't cleared
    # (though it is cleared now)
    unique_suffix = int(datetime.now(timezone.utc).timestamp())
    bidding_data = Bidding(
        process_number=f"CASCADE_TEST_{unique_suffix}",
        city="Cascade Test City",
        mode=BiddingMode.PE,
        date=datetime.now(timezone.utc)
    )
    created_bidding = bidding_repo.add(bidding_data)
    assert created_bidding and created_bidding.id is not None, "Failed to create Bidding"
    bidding_id = created_bidding.id
    print(f"Created Bidding with ID: {bidding_id}")

    item1_data = Item(name="Item 1 (Cascade Test)", code=f"CTI1_{unique_suffix}", unit="pcs", quantity=100, bidding_id=bidding_id, notes="Item 1 for cascade delete test")
    created_item1 = item_repo.add(item1_data)
    assert created_item1 and created_item1.id is not None, "Failed to create Item 1"
    item1_id = created_item1.id
    print(f"Created Item 1 with ID: {item1_id} for Bidding ID: {bidding_id}")

    item2_data = Item(name="Item 2 (Cascade Test)", code=f"CTI2_{unique_suffix}", unit="box", quantity=20, bidding_id=bidding_id, notes="Item 2 for cascade delete test")
    created_item2 = item_repo.add(item2_data)
    assert created_item2 and created_item2.id is not None, "Failed to create Item 2"
    item2_id = created_item2.id
    print(f"Created Item 2 with ID: {item2_id} for Bidding ID: {bidding_id}")

    quote1_item1_data = Quote(item_id=item1_id, supplier_id=test_supplier.id, price=Decimal("12.34"), margin=0.15) # margin is float
    created_quote1 = quote_repo.add(quote1_item1_data)
    assert created_quote1 and created_quote1.id is not None, "Failed to create Quote 1 for Item 1"
    quote1_id = created_quote1.id
    print(f"Created Quote 1 (ID: {quote1_id}) for Item ID: {item1_id}")

    bid1_item1_data = Bid(item_id=item1_id, bidding_id=bidding_id, bidder_id=test_bidder.id, price=Decimal("11.99"))
    created_bid1 = bid_repo.add(bid1_item1_data)
    assert created_bid1 and created_bid1.id is not None, "Failed to create Bid 1 for Item 1"
    bid1_id = created_bid1.id
    print(f"Created Bid 1 (ID: {bid1_id}) for Item ID: {item1_id}")

    quote2_item2_data = Quote(item_id=item2_id, supplier_id=test_supplier.id, price=Decimal("56.78"), margin=0.20) # margin is float
    created_quote2 = quote_repo.add(quote2_item2_data)
    assert created_quote2 and created_quote2.id is not None, "Failed to create Quote 2 for Item 2"
    quote2_id = created_quote2.id
    print(f"Created Quote 2 (ID: {quote2_id}) for Item ID: {item2_id}")

    assert bidding_repo.get(bidding_id) is not None, f"Bidding {bidding_id} not found before delete."
    assert item_repo.get(item1_id) is not None, f"Item {item1_id} not found before delete."
    assert item_repo.get(item2_id) is not None, f"Item {item2_id} not found before delete."
    assert quote_repo.get(quote1_id) is not None, f"Quote {quote1_id} not found before delete."
    assert bid_repo.get(bid1_id) is not None, f"Bid {bid1_id} not found before delete."
    assert quote_repo.get(quote2_id) is not None, f"Quote {quote2_id} not found before delete."
    print("All test records created and verified successfully.")

    print(f"\nStep 3: Deleting Bidding with ID: {bidding_id}...")
    delete_op_successful = bidding_repo.delete(bidding_id)
    assert delete_op_successful, f"Repository delete call failed for Bidding ID: {bidding_id}"
    print(f"Delete operation for Bidding ID: {bidding_id} reported success.")

    print("\nStep 4: Verifying cascade deletion for all related entities...")
    assert bidding_repo.get(bidding_id) is None, f"Bidding ID {bidding_id} was found in DB after delete."
    print(f"OK: Bidding ID {bidding_id} correctly not found.")

    assert item_repo.get(item1_id) is None, f"Item 1 ID {item1_id} (belonging to Bidding {bidding_id}) was found after Bidding delete."
    print(f"OK: Item 1 ID {item1_id} correctly not found.")
    assert item_repo.get(item2_id) is None, f"Item 2 ID {item2_id} (belonging to Bidding {bidding_id}) was found after Bidding delete."
    print(f"OK: Item 2 ID {item2_id} correctly not found.")

    assert quote_repo.get(quote1_id) is None, f"Quote 1 ID {quote1_id} (belonging to Item {item1_id}) was found after Item/Bidding delete."
    print(f"OK: Quote 1 ID {quote1_id} correctly not found.")
    assert bid_repo.get(bid1_id) is None, f"Bid 1 ID {bid1_id} (belonging to Item {item1_id}) was found after Item/Bidding delete."
    print(f"OK: Bid 1 ID {bid1_id} correctly not found.")
    assert quote_repo.get(quote2_id) is None, f"Quote 2 ID {quote2_id} (belonging to Item {item2_id}) was found after Item/Bidding delete."
    print(f"OK: Quote 2 ID {quote2_id} correctly not found.")

    print("\nCascade delete test completed successfully for all levels!")

if __name__ == "__main__":
    print(f"Executing test script from: {os.path.abspath(__file__)}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    # print(f"SQLAlchemy version: {sa.__version__}") # sa might not be defined if script fails before its import

    # Add src to path relative to this script's location if it's not already findable
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir)) # Assumes script is in project root
    src_path = os.path.join(project_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    if project_root not in sys.path: # To find test_cascade_delete itself if needed by runner
        sys.path.insert(0, project_root)
    # print(f"Sys.path includes: {src_path} and {project_root}") # Reduced verbosity

    try:
        # Print SQLAlchemy version after ensuring sa is imported
        if 'sa' in globals() or 'sa' in locals():
             print(f"SQLAlchemy version: {sa.__version__}")
        else:
             import sqlalchemy as sa_local
             print(f"SQLAlchemy version (loaded for print): {sa_local.__version__}")

        run_cascade_delete_test()
        print("TEST PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: Assertion Error - {e}")
        # The raise will propagate the error, causing non-zero exit code.
        raise
    except Exception as e:
        print(f"TEST FAILED: An unexpected error occurred - {type(e).__name__}: {e}")
        # The raise will propagate the error, causing non-zero exit code.
        raise
