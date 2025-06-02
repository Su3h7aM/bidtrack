import pandas as pd
from decimal import Decimal
from datetime import datetime, timezone
import pytest
import numpy as np # For np.nan, though pd.NA is preferred

from src.db.models import Quote, Supplier, Bid, Bidder # Added Bid, Bidder
from src.services.dataframes import get_quotes_dataframe, get_bids_dataframe # Added get_bids_dataframe

# --- Mock Data ---
MOCK_SUPPLIERS = [
    Supplier(id=1, name="Supplier Foo", 
             created_at=datetime.now(timezone.utc), 
             updated_at=datetime.now(timezone.utc), 
             website="foo.com", email="foo@sfoo.com", phone="123", desc="desc")
]

MOCK_BIDDERS = [
    Bidder(id=1, name="Bidder Alpha", 
           created_at=datetime.now(timezone.utc), 
           updated_at=datetime.now(timezone.utc), 
           website="alpha.co", email="contact@alpha.co", phone="111", desc="Alpha desc"),
    Bidder(id=2, name="Bidder Bravo", 
           created_at=datetime.now(timezone.utc), 
           updated_at=datetime.now(timezone.utc), 
           website="bravo.co", email="contact@bravo.co", phone="222", desc="Bravo desc")
]

# --- Expected Column Definitions for Empty DataFrames ---
# Based on current implementation of get_quotes_dataframe
EXPECTED_EMPTY_QUOTES_DF_COLS = [
    "supplier_name", "price", "created_at", "update_at", "notes"
]
# Based on current implementation of get_bids_dataframe
EXPECTED_EMPTY_BIDS_DF_COLS = [
    "bidder_name", "price", "created_at", "notes", "update_at"
]

# --- Expected Column Definitions for Non-Empty DataFrames ---
EXPECTED_QUOTES_DF_COLS_NON_EMPTY = [
    "supplier_name", "price", "freight", "additional_costs", "taxes", "margin",
    "calculated_price", "created_at", "update_at", "notes", "id", "item_id", "supplier_id"
]
EXPECTED_BIDS_DF_COLS_NON_EMPTY = [
    "bidder_name", "price", "created_at", "notes", "update_at", "id", 
    "item_id", "bidding_id", "bidder_id"
]


# --- Tests for get_quotes_dataframe ---
def test_get_quotes_dataframe_basic_calculation():
    quotes_list = [
        Quote(id=1, item_id=1, supplier_id=1, price=Decimal("100.00"),
              freight=Decimal("10.00"), additional_costs=Decimal("5.00"),
              taxes=Decimal("10.00"), margin=Decimal("20.00"), 
              notes="Test basic calc", 
              created_at=datetime.now(timezone.utc), 
              updated_at=datetime.now(timezone.utc))
    ]
    result_df = get_quotes_dataframe(quotes_list, MOCK_SUPPLIERS)
    
    assert "calculated_price" in result_df.columns
    expected_value = 115 / 0.70 
    assert result_df["calculated_price"].iloc[0] == pytest.approx(expected_value)
    assert result_df["price"].iloc[0] == pytest.approx(100.0)
    assert result_df["freight"].iloc[0] == pytest.approx(10.0)
    assert result_df["additional_costs"].iloc[0] == pytest.approx(5.0)
    assert result_df["taxes"].iloc[0] == pytest.approx(10.0)
    assert result_df["margin"].iloc[0] == pytest.approx(20.0)
    assert result_df["supplier_name"].iloc[0] == "Supplier Foo"
    for col in EXPECTED_QUOTES_DF_COLS_NON_EMPTY:
        assert col in result_df.columns

def test_get_quotes_dataframe_zero_values():
    quotes_list = [
        Quote(id=2, item_id=1, supplier_id=1, price=Decimal("100.00"),
              freight=Decimal("0.00"), additional_costs=Decimal("0.00"),
              taxes=Decimal("0.00"), margin=Decimal("0.00"), 
              notes="Test zero values", 
              created_at=datetime.now(timezone.utc), 
              updated_at=datetime.now(timezone.utc))
    ]
    result_df = get_quotes_dataframe(quotes_list, MOCK_SUPPLIERS)
    assert "calculated_price" in result_df.columns
    expected_value = 100.0
    assert result_df["calculated_price"].iloc[0] == pytest.approx(expected_value)

def test_get_quotes_dataframe_denominator_zero():
    quotes_list = [
        Quote(id=3, item_id=1, supplier_id=1, price=Decimal("100.00"),
              freight=Decimal("0.00"), additional_costs=Decimal("0.00"),
              taxes=Decimal("50.00"), margin=Decimal("50.00"),
              notes="Test denominator zero", 
              created_at=datetime.now(timezone.utc), 
              updated_at=datetime.now(timezone.utc))
    ]
    result_df = get_quotes_dataframe(quotes_list, MOCK_SUPPLIERS)
    assert "calculated_price" in result_df.columns
    assert pd.isna(result_df["calculated_price"].iloc[0])

def test_get_quotes_dataframe_denominator_negative():
    quotes_list = [
        Quote(id=4, item_id=1, supplier_id=1, price=Decimal("100.00"),
              freight=Decimal("0.00"), additional_costs=Decimal("0.00"),
              taxes=Decimal("60.00"), margin=Decimal("50.00"),
              notes="Test denominator negative", 
              created_at=datetime.now(timezone.utc), 
              updated_at=datetime.now(timezone.utc))
    ]
    result_df = get_quotes_dataframe(quotes_list, MOCK_SUPPLIERS)
    assert "calculated_price" in result_df.columns
    assert pd.isna(result_df["calculated_price"].iloc[0])

def test_get_quotes_dataframe_empty_list():
    result_df = get_quotes_dataframe([], MOCK_SUPPLIERS) 
    assert result_df.empty
    assert list(result_df.columns) == EXPECTED_EMPTY_QUOTES_DF_COLS
    assert "calculated_price" not in result_df.columns

def test_get_quotes_dataframe_multiple_quotes():
    quotes_list = [
        Quote(id=5, item_id=1, supplier_id=1, price=Decimal("100.00"), freight=Decimal("10.00"), additional_costs=Decimal("5.00"), taxes=Decimal("10.00"), margin=Decimal("20.00"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
        Quote(id=6, item_id=2, supplier_id=1, price=Decimal("200.00"), freight=Decimal("0.00"), additional_costs=Decimal("0.00"), taxes=Decimal("50.00"), margin=Decimal("50.00"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
    ]
    result_df = get_quotes_dataframe(quotes_list, MOCK_SUPPLIERS)
    assert len(result_df) == 2
    assert result_df.loc[result_df['id'] == 5, "calculated_price"].iloc[0] == pytest.approx(115 / 0.70)
    assert pd.isna(result_df.loc[result_df['id'] == 6, "calculated_price"].iloc[0])
    for col in EXPECTED_QUOTES_DF_COLS_NON_EMPTY:
        assert col in result_df.columns

# --- Tests for get_bids_dataframe ---

def test_get_bids_dataframe_empty_list():
    result_df = get_bids_dataframe([], [])
    assert result_df.empty
    assert list(result_df.columns) == EXPECTED_EMPTY_BIDS_DF_COLS

def test_get_bids_dataframe_basic():
    bids_list = [
        Bid(id=1, item_id=1, bidding_id=1, price=Decimal("100.00"), bidder_id=1, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
        Bid(id=2, item_id=2, bidding_id=1, price=Decimal("150.00"), bidder_id=2, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    ]
    result_df = get_bids_dataframe(bids_list, MOCK_BIDDERS)
    assert len(result_df) == 2
    assert result_df.loc[result_df['id'] == 1, "bidder_name"].iloc[0] == "Bidder Alpha"
    assert result_df.loc[result_df['id'] == 2, "bidder_name"].iloc[0] == "Bidder Bravo"
    for col in EXPECTED_BIDS_DF_COLS_NON_EMPTY:
        assert col in result_df.columns

def test_get_bids_dataframe_no_bidder():
    bids_list = [
        Bid(id=3, item_id=1, bidding_id=1, price=Decimal("100.00"), 
            bidder_id=None, # Explicitly None
            notes="Bid with no bidder", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    ]
    # Pass MOCK_BIDDERS or empty list, result for this bid should be "N/D"
    result_df = get_bids_dataframe(bids_list, MOCK_BIDDERS) 
    
    assert "bidder_name" in result_df.columns
    assert result_df["bidder_name"].iloc[0] == "N/D"
    assert pd.isna(result_df["bidder_id"].iloc[0]) # bidder_id remains None/NaN
    for col in EXPECTED_BIDS_DF_COLS_NON_EMPTY: # Check all columns are there
        if col not in ['bidder_id'] : # bidder_id will be NaN/None for this row
             assert pd.notna(result_df[col].iloc[0]) or isinstance(result_df[col].iloc[0], str)


def test_get_bids_dataframe_mixed_bidders():
    bids_list = [
        Bid(id=4, item_id=1, bidding_id=1, price=Decimal("100.00"), 
            bidder_id=1, # Linked to Bidder Alpha
            notes="Bid from Alpha", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
        Bid(id=5, item_id=2, bidding_id=1, price=Decimal("200.00"), 
            bidder_id=None, 
            notes="Bid with no bidder", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    ]
    result_df = get_bids_dataframe(bids_list, MOCK_BIDDERS)
    
    assert len(result_df) == 2
    assert result_df.loc[result_df['id'] == 4, "bidder_name"].iloc[0] == "Bidder Alpha"
    assert result_df.loc[result_df['id'] == 4, "bidder_id"].iloc[0] == 1.0 # Pandas converts int to float if NaNs are present in column
    
    assert result_df.loc[result_df['id'] == 5, "bidder_name"].iloc[0] == "N/D"
    assert pd.isna(result_df.loc[result_df['id'] == 5, "bidder_id"].iloc[0])
    
    for col in EXPECTED_BIDS_DF_COLS_NON_EMPTY:
        assert col in result_df.columns
```
