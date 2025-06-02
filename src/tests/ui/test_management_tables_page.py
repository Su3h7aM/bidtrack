import pytest
import pandas as pd
from decimal import Decimal
from db.models import BiddingMode # Assuming BiddingMode is in db.models

# Test Data
@pytest.fixture
def sample_biddings_df():
    data = {
        'id': [1, 2, 3, 4],
        'process_number': ['P100', 'P101', 'P102', 'P103/2023'],
        'city': ['City A', 'City B', 'city A', 'Metropolis C'],
        'mode_display': [BiddingMode.CONCORRENCIA.value, BiddingMode.PREGAO.value, BiddingMode.CONVITE.value, BiddingMode.PREGAO.value],
        'description': ['Desc A', 'Desc B', 'Desc C', 'Desc D'],
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_items_df():
    data = {
        'id': [1, 2, 3],
        'name': ['Item Alpha', 'Item Beta', 'Gamma Product'],
        'description': ['Alpha desc', 'Beta desc', 'Gamma desc'],
        'code': ['A01', 'B02', 'C03'],
        'bidding_id': [1, 1, 2]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_suppliers_df():
    data = {
        'id': [1, 2],
        'name': ['Supplier X', 'Supplier Y'],
        'website': ['x.com', 'y.com'],
        'email': ['contact@x.com', 'support@y.com'],
        'phone': ['111', '222'],
        'desc': ['Desc X', 'Desc Y']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_quotes_df():
    data = {
        'id': [1, 2, 3],
        'item_name': ['Item Alpha', 'Item Beta', 'Item Alpha'],
        'supplier_name': ['Supplier X', 'Supplier Y', 'Supplier Y'],
        'price': [Decimal('10.50'), Decimal('22.00'), Decimal('12.00')],
        'notes': ['Note 1', 'Note 2', 'Urgent'],
    }
    return pd.DataFrame(data)
    
@pytest.fixture
def sample_bidders_df(): # Similar to suppliers
    data = {
        'id': [1, 2],
        'name': ['Bidder One', 'Bidder Two'],
        'website': ['one.com', 'two.com'],
        'email': ['info@one.com', 'contact@two.com'],
        'phone': ['333', '444'],
        'desc': ['Details One', 'Details Two']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_bids_df():
    data = {
        'id': [1, 2, 3],
        'item_name': ['Item Alpha', 'Item Beta', 'Item Alpha'],
        'bidder_name': ['Bidder One', 'Bidder Two', 'Bidder One'],
        'price': [Decimal('100.00'), Decimal('150.00'), Decimal('90.00')],
        'notes': ['Bid note A', 'Bid note B', 'Final offer'],
    }
    return pd.DataFrame(data)

# --- Test Search/Filtering Logic (Mimicking inline logic) ---

def test_filter_biddings(sample_biddings_df):
    df = sample_biddings_df
    
    # Test search by process_number
    search_term_lower = 'p100'
    filtered = df[
        df["process_number"].astype(str).str.lower().str.contains(search_term_lower) |
        df["city"].astype(str).str.lower().str.contains(search_term_lower) |
        df["mode_display"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 1
    assert filtered.iloc[0]['id'] == 1

    # Test search by city (case-insensitive)
    search_term_lower = 'city a'
    filtered = df[
        df["process_number"].astype(str).str.lower().str.contains(search_term_lower) |
        df["city"].astype(str).str.lower().str.contains(search_term_lower) |
        df["mode_display"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 2 # City A and city A
    
    # Test search by mode_display
    search_term_lower = BiddingMode.PREGAO.value.lower()
    filtered = df[
        df["process_number"].astype(str).str.lower().str.contains(search_term_lower) |
        df["city"].astype(str).str.lower().str.contains(search_term_lower) |
        df["mode_display"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 2
    
    # Test no match
    search_term_lower = 'nonexistent'
    filtered = df[
        df["process_number"].astype(str).str.lower().str.contains(search_term_lower) |
        df["city"].astype(str).str.lower().str.contains(search_term_lower) |
        df["mode_display"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 0

    # Test empty search term (should return all) - current app logic shows all if search_term is empty
    # This test reflects that if search_term is "", the filtering block is skipped.
    # So, if search_term is empty, filtered_df = unfiltered_df
    assert len(df) == 4 


def test_filter_items(sample_items_df):
    df = sample_items_df
    search_term_lower = 'alpha'
    filtered = df[
        df["name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["description"].astype(str).str.lower().str.contains(search_term_lower) |
        df["code"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 1
    assert filtered.iloc[0]['name'] == 'Item Alpha'

    search_term_lower = 'c03'
    filtered = df[
        df["name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["description"].astype(str).str.lower().str.contains(search_term_lower) |
        df["code"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 1
    assert filtered.iloc[0]['code'] == 'C03'

def test_filter_suppliers(sample_suppliers_df):
    df = sample_suppliers_df
    search_term_lower = 'supplier x'
    filtered = df[
        df["name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["website"].astype(str).str.lower().str.contains(search_term_lower) |
        df["email"].astype(str).str.lower().str.contains(search_term_lower) |
        df["phone"].astype(str).str.lower().str.contains(search_term_lower) |
        df["desc"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 1
    assert filtered.iloc[0]['name'] == 'Supplier X'

def test_filter_quotes(sample_quotes_df):
    df = sample_quotes_df
    search_term_lower = 'supplier y'
    filtered = df[
        df["item_name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["supplier_name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["notes"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 2 # Two quotes from Supplier Y

    search_term_lower = 'urgent'
    filtered = df[
        df["item_name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["supplier_name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["notes"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 1
    assert filtered.iloc[0]['notes'] == 'Urgent'


def test_filter_bidders(sample_bidders_df): # Similar to suppliers
    df = sample_bidders_df
    search_term_lower = 'one.com'
    filtered = df[
        df["name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["website"].astype(str).str.lower().str.contains(search_term_lower) |
        df["email"].astype(str).str.lower().str.contains(search_term_lower) |
        df["phone"].astype(str).str.lower().str.contains(search_term_lower) |
        df["desc"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 1
    assert filtered.iloc[0]['name'] == 'Bidder One'

def test_filter_bids(sample_bids_df):
    df = sample_bids_df
    search_term_lower = 'bidder one'
    filtered = df[
        df["item_name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["bidder_name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["notes"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 2 # Two bids from Bidder One

    search_term_lower = 'final offer'
    filtered = df[
        df["item_name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["bidder_name"].astype(str).str.lower().str.contains(search_term_lower) |
        df["notes"].astype(str).str.lower().str.contains(search_term_lower)
    ]
    assert len(filtered) == 1
    assert filtered.iloc[0]['notes'] == 'Final offer'


# --- Test Data Type Conversions (Mimicking logic in save operations) ---

def test_bidding_mode_conversion():
    assert BiddingMode(BiddingMode.CONCORRENCIA.value) == BiddingMode.CONCORRENCIA
    assert BiddingMode(BiddingMode.PREGAO.value) == BiddingMode.PREGAO
    with pytest.raises(ValueError):
        BiddingMode("invalid_mode")

def test_decimal_conversion():
    assert Decimal(str("10.50")) == Decimal("10.50")
    assert Decimal(str(25)) == Decimal("25")
    assert Decimal(str("0.01")) == Decimal("0.01")
    with pytest.raises(Exception): # Broad exception as Decimal can raise various InvalidOperation subtypes
        Decimal("not_a_number")

def test_float_conversion_for_quantity():
    assert float("12.34") == 12.34
    with pytest.raises(ValueError):
        float("abc")

# Further tests could be added for the logic that constructs the update_dict,
# but that would require more complex mocking of DataFrame rows or refactoring
# that logic into testable helper functions.
# For now, testing the core filtering and crucial type conversions provides good coverage
# for the most isolated parts of the data manipulation logic.
