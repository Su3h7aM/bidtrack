import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from decimal import Decimal

from src.db.models import Quote, Supplier, Item, Bid, Bidder # Assuming these are the model classes
from src.services.dataframes import get_quotes_dataframe, get_bids_dataframe

# --- Fixtures for sample model instances ---

@pytest.fixture
def sample_items():
    return [
        Item(id=1, name="Laptop", bidding_id=1, description="High-end laptop", code="LP001", quantity=10, unit="pcs"),
        Item(id=2, name="Mouse", bidding_id=1, description="Wireless mouse", code="MS002", quantity=20, unit="pcs"),
        Item(id=3, name="Keyboard", bidding_id=2, description="Mechanical keyboard", code="KB003", quantity=15, unit="pcs"),
    ]

@pytest.fixture
def sample_suppliers():
    return [
        Supplier(id=1, name="Tech Solutions Ltd.", website="tech.com", email="contact@tech.com", phone="123", desc="Supplies tech"),
        Supplier(id=2, name="Office Gear Inc.", website="office.com", email="sales@office.com", phone="456", desc="Supplies office items"),
    ]

@pytest.fixture
def sample_bidders():
    return [
        Bidder(id=1, name="BidMaster Pro", website="bidmaster.com", email="info@bidmaster.com", phone="789", desc="Professional bidder"),
        Bidder(id=2, name="TenderPro Services", website="tender.pro", email="contact@tender.pro", phone="012", desc="Tender specialist"),
    ]

@pytest.fixture
def sample_quotes(sample_items, sample_suppliers):
    # Quotes for item 1 (Laptop) from supplier 1 and 2
    # Quote for item 2 (Mouse) from supplier 1
    return [
        Quote(id=1, item_id=1, supplier_id=1, price=Decimal("1200.00"), freight=Decimal("50.00"), additional_costs=Decimal("10.00"), taxes=Decimal("10"), margin=Decimal("20"), notes="Laptop quote 1", created_at=pd.Timestamp("2023-01-01")),
        Quote(id=2, item_id=1, supplier_id=2, price=Decimal("1150.00"), freight=Decimal("40.00"), additional_costs=Decimal("5.00"), taxes=Decimal("10"), margin=Decimal("18"), notes="Laptop quote 2", created_at=pd.Timestamp("2023-01-02")),
        Quote(id=3, item_id=2, supplier_id=1, price=Decimal("25.00"), freight=Decimal("5.00"), additional_costs=Decimal("1.00"), taxes=Decimal("5"), margin=Decimal("15"), notes="Mouse quote", created_at=pd.Timestamp("2023-01-03")),
    ]

@pytest.fixture
def sample_bids(sample_items, sample_bidders):
    # Bids for item 1 (Laptop) from bidder 1 and 2
    # Bid for item 2 (Mouse) from bidder 1
    return [
        Bid(id=1, item_id=1, bidding_id=1, bidder_id=1, price=Decimal("1000.00"), notes="Bid for Laptop 1", created_at=pd.Timestamp("2023-01-10")),
        Bid(id=2, item_id=1, bidding_id=1, bidder_id=2, price=Decimal("950.00"), notes="Bid for Laptop 2", created_at=pd.Timestamp("2023-01-11")),
        Bid(id=3, item_id=2, bidding_id=1, bidder_id=1, price=Decimal("20.00"), notes="Bid for Mouse", created_at=pd.Timestamp("2023-01-12")),
        Bid(id=4, item_id=1, bidding_id=1, bidder_id=None, price=Decimal("1100.00"), notes="Anonymous bid", created_at=pd.Timestamp("2023-01-13")), # Test None bidder_id
    ]

# --- Tests for get_quotes_dataframe ---

def test_get_quotes_dataframe_empty():
    df = get_quotes_dataframe([], [], [])
    assert df.empty
    expected_cols = ["id", "item_id", "supplier_id", "price", "freight", "additional_costs", "taxes", "margin", "notes", "created_at", "updated_at", "supplier_name", "item_name", "calculated_price"]
    assert list(df.columns) == expected_cols

def test_get_quotes_dataframe_with_data(sample_quotes, sample_suppliers, sample_items):
    df = get_quotes_dataframe(sample_quotes, sample_suppliers, sample_items)

    assert len(df) == 3
    assert "item_name" in df.columns
    assert "supplier_name" in df.columns
    assert "calculated_price" in df.columns

    # Check item_name and supplier_name mapping
    assert df.loc[df['id'] == 1, "item_name"].iloc[0] == "Laptop"
    assert df.loc[df['id'] == 1, "supplier_name"].iloc[0] == "Tech Solutions Ltd."
    assert df.loc[df['id'] == 3, "item_name"].iloc[0] == "Mouse"

    # Check calculated_price for one entry (Quote ID 1)
    # P=1200, F=50, AC=10 => DirectCost = 1260
    # T=10%, M=20%
    # PriceWithTax = 1260 * (1 + 0.10) = 1260 * 1.1 = 1386
    # FinalPrice = 1386 * (1 + 0.20) = 1386 * 1.2 = 1663.20
    expected_price_quote1 = Decimal("1663.20")
    assert df.loc[df['id'] == 1, "calculated_price"].iloc[0] == expected_price_quote1
    assert isinstance(df.loc[df['id'] == 1, "calculated_price"].iloc[0], Decimal)

    # Check date types (should be naive datetime)
    assert pd.api.types.is_datetime64_ns_dtype(df['created_at'])
    assert df['created_at'].iloc[0].tzinfo is None

    # Check all expected columns are present
    expected_cols = ["id", "item_name", "supplier_name", "price", "freight", "additional_costs", "taxes", "margin", "calculated_price", "notes", "item_id", "supplier_id", "created_at", "updated_at"]
    for col in expected_cols:
        assert col in df.columns

# --- Tests for get_bids_dataframe ---

def test_get_bids_dataframe_empty():
    df = get_bids_dataframe([], [], [])
    assert df.empty
    expected_cols = ["id", "item_id", "bidding_id", "bidder_id", "price", "notes", "created_at", "updated_at", "item_name", "bidder_name"]
    assert list(df.columns) == expected_cols

def test_get_bids_dataframe_with_data(sample_bids, sample_bidders, sample_items):
    df = get_bids_dataframe(sample_bids, sample_bidders, sample_items)

    assert len(df) == 4 # Including the anonymous bid
    assert "item_name" in df.columns
    assert "bidder_name" in df.columns

    # Check item_name and bidder_name mapping
    assert df.loc[df['id'] == 1, "item_name"].iloc[0] == "Laptop"
    assert df.loc[df['id'] == 1, "bidder_name"].iloc[0] == "BidMaster Pro"
    assert df.loc[df['id'] == 3, "item_name"].iloc[0] == "Mouse"
    assert df.loc[df['id'] == 4, "bidder_name"].iloc[0] == "Licitante Desconhecido" # For None bidder_id

    # Check date types (should be naive datetime)
    assert pd.api.types.is_datetime64_ns_dtype(df['created_at'])
    assert df['created_at'].iloc[0].tzinfo is None

    # Check price type
    assert isinstance(df.loc[df['id'] == 1, "price"].iloc[0], Decimal)

    # Check all expected columns are present
    expected_cols = ["id", "item_name", "bidder_name", "price", "notes", "item_id", "bidding_id", "bidder_id", "created_at", "updated_at"]
    for col in expected_cols:
        assert col in df.columns

def test_get_bids_dataframe_no_bidders_list(sample_bids, sample_items):
    # Test when bidders_list is empty
    df = get_bids_dataframe(sample_bids, [], sample_items)
    assert len(df) == 4
    assert "bidder_name" in df.columns
    assert all(df["bidder_name"] == "Licitante Desconhecido")

def test_get_bids_dataframe_no_items_list(sample_bids, sample_bidders):
    # Test when items_list is empty
    df = get_bids_dataframe(sample_bids, sample_bidders, [])
    assert len(df) == 4
    assert "item_name" in df.columns
    assert all(df["item_name"] == "Item Desconhecido")

# Further tests could include:
# - Quotes/Bids with missing optional fields (e.g., notes, freight) to ensure they are handled.
# - Suppliers/Bidders/Items with missing optional fields.
# - Data that might cause issues with Decimal conversion (though to_decimal_safe should handle it).
# Phase 3 (Create Tests for `src/services/dataframes.py`) is complete. I've created `tests/services/test_dataframes.py` with:
# -   Fixtures for sample `Item`, `Supplier`, `Bidder`, `Quote`, and `Bid` model objects.
# -   Tests for `get_quotes_dataframe`:
#     -   Handling of empty input lists.
#     -   Correct DataFrame structure, `item_name`/`supplier_name` mapping, `calculated_price` logic (asserting specific Decimal value), and date types with sample data.
# -   Tests for `get_bids_dataframe`:
#     -   Handling of empty input lists.
#     -   Correct DataFrame structure, `item_name`/`bidder_name` mapping (including `None` bidder_id), date types, and price type (Decimal) with sample data.
#     -   Cases where `bidders_list` or `items_list` might be empty.

# Now, I'll proceed to Phase 4: Create tests for `src/ui/utils.py` in `tests/ui/test_utils.py`.
